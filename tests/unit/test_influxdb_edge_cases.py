import unittest
from unittest.mock import patch, Mock, MagicMock
import numpy as np
import pandas as pd
from datetime import datetime
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError
import pytest

import sys
sys.path.insert(0, '/home/cristiantr/GitHub/ctrutils')

from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from tests.fixtures.influxdb_fixtures import (
    create_mock_influxdb_client,
    create_edge_case_dataframe,
    create_edge_case_points,
    create_malformed_query_examples,
    create_connection_failure_scenarios,
    create_batch_size_scenarios,
)


@pytest.mark.unit
@pytest.mark.edge_case
class TestInfluxdbConnectionEdgeCases(unittest.TestCase):
    def test_init_with_invalid_host(self):
        with self.assertRaises((ValueError, TypeError, InfluxDBClientError)):
            InfluxdbOperation(
                host='',
                port=8086,
                username='admin',
                password='admin',
                database='test_db'
            )

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_init_with_invalid_port_zero(self, mock_client_class):
        mock_client = create_mock_influxdb_client()
        mock_client_class.return_value = mock_client

        influx_op = InfluxdbOperation(
            host='localhost',
            port=0,
            username='admin',
            password='admin',
            database='test_db'
        )
        self.assertIsNotNone(influx_op)

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_init_with_invalid_port_negative(self, mock_client_class):
        mock_client = create_mock_influxdb_client()
        mock_client_class.return_value = mock_client

        influx_op = InfluxdbOperation(
            host='localhost',
            port=-1,
            username='admin',
            password='admin',
            database='test_db'
        )
        self.assertIsNotNone(influx_op)

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_connection_timeout_on_ping(self, mock_client_class):
        mock_client = create_mock_influxdb_client()
        mock_client.ping.side_effect = Exception("Connection timeout")
        mock_client_class.return_value = mock_client

        with self.assertRaises(Exception):
            InfluxdbOperation(
                host='localhost',
                port=8086,
                username='admin',
                password='admin',
                database='test_db'
            )

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_external_client_lifecycle(self, mock_client_class):
        external_client = create_mock_influxdb_client()

        influx_op = InfluxdbOperation(
            client=external_client,
            database='test_db'
        )

        self.assertEqual(influx_op.client, external_client)

        influx_op.close()
        external_client.close.assert_not_called()

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_switch_database_creates_if_not_exists(self, mock_client_class):
        mock_client = create_mock_influxdb_client(
            get_list_database_return=[{'name': 'existing_db'}]
        )
        mock_client_class.return_value = mock_client

        influx_op = InfluxdbOperation(
            host='localhost',
            port=8086,
            username='admin',
            password='admin',
            database='test_db'
        )

        influx_op.switch_database('new_db')

        mock_client.create_database.assert_called_with('new_db')
        mock_client.switch_database.assert_called_with('new_db')


@pytest.mark.unit
@pytest.mark.edge_case
class TestInfluxdbDataNormalizationEdgeCases(unittest.TestCase):

    def setUp(self):
        mock_client = create_mock_influxdb_client()
        self.influx_op = InfluxdbOperation(client=mock_client, database='test_db')

    def test_normalize_positive_infinity(self):
        value = float('inf')
        normalized = self.influx_op.normalize_value_to_write(value)
        self.assertIsNone(normalized)

    def test_normalize_negative_infinity(self):
        value = float('-inf')
        normalized = self.influx_op.normalize_value_to_write(value)
        self.assertIsNone(normalized)

    def test_normalize_numpy_nan(self):
        value = np.nan
        normalized = self.influx_op.normalize_value_to_write(value)
        self.assertIsNone(normalized)

    def test_normalize_pandas_na(self):
        value = pd.NA
        normalized = self.influx_op.normalize_value_to_write(value)
        self.assertIsNone(normalized)

    def test_normalize_none(self):
        value = None
        normalized = self.influx_op.normalize_value_to_write(value)
        self.assertIsNone(normalized)

    def test_normalize_very_large_positive_number(self):
        value = 1e308
        normalized = self.influx_op.normalize_value_to_write(value)
        self.assertEqual(normalized, value)

    def test_normalize_very_large_negative_number(self):
        value = -1e308
        normalized = self.influx_op.normalize_value_to_write(value)
        self.assertEqual(normalized, value)

    def test_normalize_very_small_positive_number(self):
        value = 1e-308
        normalized = self.influx_op.normalize_value_to_write(value)
        self.assertEqual(normalized, value)

    def test_normalize_very_small_negative_number(self):
        value = -1e-308
        normalized = self.influx_op.normalize_value_to_write(value)
        self.assertEqual(normalized, value)

    def test_normalize_unicode_string(self):
        test_cases = ['北京', 'Москва', 'café', '🌡️', 'θερμοκρασία']
        for value in test_cases:
            normalized = self.influx_op.normalize_value_to_write(value)
            self.assertEqual(normalized, value)

    def test_normalize_empty_string(self):
        value = ''
        normalized = self.influx_op.normalize_value_to_write(value)
        self.assertEqual(normalized, value)

    def test_normalize_whitespace_string(self):
        value = '   '
        normalized = self.influx_op.normalize_value_to_write(value)
        self.assertEqual(normalized, value)

    def test_normalize_numpy_int_types(self):
        test_cases = [
            (np.int8(10), 10),
            (np.int16(100), 100),
            (np.int32(1000), 1000),
            (np.int64(10000), 10000),
        ]
        for value, expected in test_cases:
            normalized = self.influx_op.normalize_value_to_write(value)
            self.assertEqual(normalized, expected)

    def test_normalize_numpy_float_types(self):
        test_cases = [
            (np.float32(1.5), 1.5),
            (np.float64(2.5), 2.5),
        ]
        for value, expected in test_cases:
            normalized = self.influx_op.normalize_value_to_write(value)
            self.assertAlmostEqual(normalized, expected, places=5)


@pytest.mark.unit
@pytest.mark.edge_case
class TestInfluxdbWriteEdgeCases(unittest.TestCase):

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_write_empty_dataframe(self, mock_client_class):
        mock_client = create_mock_influxdb_client()
        mock_client_class.return_value = mock_client

        influx_op = InfluxdbOperation(client=mock_client, database='test_db')
        df = create_edge_case_dataframe('empty')

        result = influx_op.write_dataframe(df, measurement='test')

        self.assertIsNotNone(result)
        mock_client.write_points.assert_not_called()

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_write_all_nan_dataframe(self, mock_client_class):
        mock_client = create_mock_influxdb_client()
        mock_client_class.return_value = mock_client

        influx_op = InfluxdbOperation(client=mock_client, database='test_db')
        df = create_edge_case_dataframe('all_nan')

        result = influx_op.write_dataframe(df, measurement='test')

        self.assertIsNotNone(result)

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_write_dataframe_with_infinity(self, mock_client_class):
        mock_client = create_mock_influxdb_client()
        mock_client_class.return_value = mock_client

        influx_op = InfluxdbOperation(client=mock_client, database='test_db')
        df = create_edge_case_dataframe('infinity')

        result = influx_op.write_dataframe(df, measurement='test')

        self.assertIsNotNone(result)
        mock_client.write_points.assert_called()

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_write_batch_size_zero(self, mock_client_class):
        mock_client = create_mock_influxdb_client()
        mock_client_class.return_value = mock_client

        influx_op = InfluxdbOperation(client=mock_client, database='test_db')
        df = pd.DataFrame({
            'value': [1.0, 2.0, 3.0]
        }, index=pd.date_range(start='2024-01-01', periods=3, freq='1min'))

        with self.assertRaises((ValueError, ZeroDivisionError)):
            influx_op.write_dataframe(df, measurement='test', batch_size=0)

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_write_with_special_char_tags(self, mock_client_class):
        mock_client = create_mock_influxdb_client()
        mock_client_class.return_value = mock_client

        influx_op = InfluxdbOperation(client=mock_client, database='test_db')
        df = create_edge_case_dataframe('special_chars')

        result = influx_op.write_dataframe(df, measurement='test', tag_columns=['tag1'])

        self.assertIsNotNone(result)

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_write_points_empty_list(self, mock_client_class):
        mock_client = create_mock_influxdb_client()
        mock_client_class.return_value = mock_client

        influx_op = InfluxdbOperation(client=mock_client, database='test_db')
        points = []

        result = influx_op.write_points(points)

        self.assertIsNotNone(result)
        mock_client.write_points.assert_not_called()

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_write_points_with_empty_fields(self, mock_client_class):
        mock_client = create_mock_influxdb_client()
        mock_client_class.return_value = mock_client

        influx_op = InfluxdbOperation(client=mock_client, database='test_db')
        points = create_edge_case_points('empty_fields')

        result = influx_op.write_points(points)

        self.assertIsNotNone(result)


@pytest.mark.unit
@pytest.mark.edge_case
class TestInfluxdbQueryEdgeCases(unittest.TestCase):

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_query_with_malformed_syntax(self, mock_client_class):
        mock_client = create_mock_influxdb_client()
        mock_client.query.side_effect = InfluxDBClientError("Invalid syntax")
        mock_client_class.return_value = mock_client

        influx_op = InfluxdbOperation(client=mock_client, database='test_db')

        malformed_queries = create_malformed_query_examples()
        for query in malformed_queries[:5]:
            with self.assertRaises(InfluxDBClientError):
                influx_op.query(query)

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_query_empty_result(self, mock_client_class):
        mock_client = create_mock_influxdb_client(query_return=MagicMock())
        mock_client.query.return_value = []
        mock_client_class.return_value = mock_client

        influx_op = InfluxdbOperation(client=mock_client, database='test_db')

        result = influx_op.query('SELECT * FROM non_existent_measurement')

        self.assertIsNotNone(result)

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_query_non_existent_measurement(self, mock_client_class):
        mock_client = create_mock_influxdb_client(query_return=[])
        mock_client_class.return_value = mock_client

        influx_op = InfluxdbOperation(client=mock_client, database='test_db')

        result = influx_op.query('SELECT * FROM measurement_that_does_not_exist')

        self.assertIsNotNone(result)

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_query_with_timeout(self, mock_client_class):
        mock_client = create_mock_influxdb_client()
        mock_client.query.side_effect = Exception("Query timeout")
        mock_client_class.return_value = mock_client

        influx_op = InfluxdbOperation(client=mock_client, database='test_db')

        with self.assertRaises(Exception):
            influx_op.query('SELECT * FROM large_measurement')


@pytest.mark.unit
@pytest.mark.edge_case
class TestInfluxdbRetryEdgeCases(unittest.TestCase):

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_retry_success_on_first_attempt(self, mock_client_class):
        mock_client = create_mock_influxdb_client()
        mock_client_class.return_value = mock_client

        influx_op = InfluxdbOperation(client=mock_client, database='test_db')

        def successful_operation():
            return "success"

        result = influx_op._retry_operation(successful_operation, max_attempts=3, backoff_factor=1)

        self.assertEqual(result, "success")

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    @patch('time.sleep', return_value=None)
    def test_retry_with_exponential_backoff(self, mock_sleep, mock_client_class):
        mock_client = create_mock_influxdb_client()
        mock_client_class.return_value = mock_client

        influx_op = InfluxdbOperation(client=mock_client, database='test_db')

        attempt_count = {'count': 0}

        def failing_then_succeeding_operation():
            attempt_count['count'] += 1
            if attempt_count['count'] < 3:
                raise Exception("Temporary failure")
            return "success"

        result = influx_op._retry_operation(failing_then_succeeding_operation, max_attempts=5, backoff_factor=2)

        self.assertEqual(result, "success")
        self.assertEqual(attempt_count['count'], 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    @patch('time.sleep', return_value=None)
    def test_retry_all_attempts_exhausted(self, mock_sleep, mock_client_class):
        mock_client = create_mock_influxdb_client()
        mock_client_class.return_value = mock_client

        influx_op = InfluxdbOperation(client=mock_client, database='test_db')

        def always_failing_operation():
            raise Exception("Permanent failure")

        with self.assertRaises(Exception) as context:
            influx_op._retry_operation(always_failing_operation, max_attempts=3, backoff_factor=1)

        self.assertIn("Permanent failure", str(context.exception))
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_retry_with_custom_max_attempts(self, mock_client_class):
        mock_client = create_mock_influxdb_client()
        mock_client_class.return_value = mock_client

        influx_op = InfluxdbOperation(client=mock_client, database='test_db')

        attempt_count = {'count': 0}

        def count_attempts():
            attempt_count['count'] += 1
            if attempt_count['count'] < 10:
                raise Exception("Keep trying")
            return "success"

        result = influx_op._retry_operation(count_attempts, max_attempts=10, backoff_factor=1)

        self.assertEqual(result, "success")
        self.assertEqual(attempt_count['count'], 10)


if __name__ == '__main__':
    unittest.main()
