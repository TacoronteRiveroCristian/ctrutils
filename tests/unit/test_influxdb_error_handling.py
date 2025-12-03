"""Tests for error handling, exceptions, and edge cases in InfluxDB operations."""
import unittest
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError
from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from tests.fixtures.influxdb_fixtures import (
    create_comprehensive_mock_client,
    create_mock_query_result,
)


@pytest.mark.unit
class TestWriteDataframeErrorHandling(unittest.TestCase):
    """Test error handling in write_dataframe method."""

    def setUp(self):
        from tests.fixtures.influxdb_fixtures import create_mock_influxdb_client
        self.mock_client = create_mock_influxdb_client(write_points_return=True)
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_write_dataframe_with_none_data_raises_error(self):
        """Test write_dataframe with None data raises ValueError."""
        with pytest.raises(ValueError, match="Debe proporcionar un DataFrame"):
            self.influx.write_dataframe(measurement='test', data=None)

    def test_write_dataframe_with_none_measurement_raises_error(self):
        """Test write_dataframe with None measurement raises ValueError."""
        df = pd.DataFrame({'value': [1, 2, 3]},
                         index=pd.date_range('2024-01-01', periods=3, freq='1min'))

        with pytest.raises(ValueError, match="Debe proporcionar un DataFrame"):
            self.influx.write_dataframe(measurement=None, data=df)

    def test_write_dataframe_with_non_datetime_index_raises_error(self):
        """Test write_dataframe with non-DatetimeIndex raises TypeError."""
        df = pd.DataFrame({'value': [1, 2, 3]})  # Default integer index

        with pytest.raises(TypeError, match="debe ser de tipo DatetimeIndex"):
            self.influx.write_dataframe(measurement='test', data=df)

    def test_write_dataframe_drop_na_rows_removes_empty(self):
        """Test write_dataframe with drop_na_rows removes fully empty rows."""
        df = pd.DataFrame({
            'value': [1.0, np.nan, 3.0],
            'value2': [np.nan, np.nan, 6.0],
        }, index=pd.date_range('2024-01-01', periods=3, freq='1min'))

        result = self.influx.write_dataframe(
            measurement='test',
            data=df,
            drop_na_rows=True
        )

        self.assertGreater(result['written_points'], 0)


@pytest.mark.unit
class TestQueryErrorHandling(unittest.TestCase):
    """Test error handling in query methods."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_get_data_with_empty_result_raises_error(self):
        """Test get_data with empty result raises ValueError."""
        mock_result = MagicMock()
        mock_result.__iter__.return_value = iter([])
        self.mock_client.query.return_value = mock_result

        with pytest.raises(ValueError, match="No hay datos disponibles"):
            self.influx.get_data('SELECT * FROM cpu')

    def test_get_data_with_client_error(self):
        """Test get_data handles client errors."""
        self.mock_client.query.side_effect = InfluxDBClientError("Query error")

        with pytest.raises(InfluxDBClientError):
            self.influx.get_data('SELECT * FROM cpu')

    def test_execute_query_builder_with_valid_result(self):
        """Test execute_query_builder with valid result."""
        points = [{'time': '2024-01-01T12:00:00Z', 'value': 1.0}]
        self.mock_client.query.return_value = create_mock_query_result(points)

        result = self.influx.execute_query_builder(measurement='cpu')
        self.assertIsNotNone(result)


@pytest.mark.unit
class TestDatabaseErrorHandling(unittest.TestCase):
    """Test error handling in database operations."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)

    def test_switch_database_without_database_param_raises_error(self):
        """Test operations without database raise ValueError."""
        influx = InfluxdbOperation(client=self.mock_client)

        with pytest.raises(ValueError, match="Debe proporcionar una base de datos"):
            influx.write_points([{'measurement': 'test', 'fields': {'value': 1}}])

    def test_drop_database_without_confirm_raises_error(self):
        """Test drop_database without confirm=True raises ValueError."""
        self.influx._database = 'test_db'

        with pytest.raises(ValueError, match="Debe confirmar"):
            self.influx.drop_database('test_db', confirm=False)

    def test_drop_measurement_without_confirm_raises_error(self):
        """Test drop_measurement without confirm=True raises ValueError."""
        self.influx._database = 'test_db'

        with pytest.raises(ValueError, match="Debe confirmar"):
            self.influx.drop_measurement('test_measurement', confirm=False)


@pytest.mark.unit
class TestBatchProcessingEdgeCases(unittest.TestCase):
    """Test batch processing with various edge cases."""

    def setUp(self):
        from tests.fixtures.influxdb_fixtures import create_mock_influxdb_client
        self.mock_client = create_mock_influxdb_client(write_points_return=True)
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_write_points_batch_size_larger_than_points(self):
        """Test write_points when batch_size > number of points."""
        points = [
            {'measurement': 'cpu', 'time': '2024-01-01T12:00:00Z', 'fields': {'value': 1.0}},
            {'measurement': 'cpu', 'time': '2024-01-01T12:01:00Z', 'fields': {'value': 2.0}},
        ]

        result = self.influx.write_points(points, batch_size=1000)

        self.assertEqual(result['batches'], 1)
        self.assertEqual(result['written_points'], 2)

    def test_write_points_exact_batch_size_multiple(self):
        """Test write_points when points exactly divide by batch_size."""
        points = [
            {'measurement': 'cpu', 'time': f'2024-01-01T12:{i:02d}:00Z', 'fields': {'value': float(i)}}
            for i in range(10)
        ]

        result = self.influx.write_points(points, batch_size=5)

        self.assertEqual(result['batches'], 2)
        self.assertEqual(result['written_points'], 10)

    def test_write_dataframe_large_batch(self):
        """Test write_dataframe with large batch size."""
        df = pd.DataFrame({
            'value': range(100),
        }, index=pd.date_range('2024-01-01', periods=100, freq='1min'))

        result = self.influx.write_dataframe(
            measurement='test',
            data=df,
            batch_size=50
        )

        self.assertGreaterEqual(result['batches'], 2)


@pytest.mark.unit
class TestNormalizeValueEdgeCases(unittest.TestCase):
    """Test normalize_value_to_write with additional edge cases."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)

    def test_normalize_very_long_string(self):
        """Test normalizing very long string."""
        long_string = 'a' * 10000
        result = self.influx.normalize_value_to_write(long_string)
        self.assertEqual(result, long_string)

    def test_normalize_string_with_newlines(self):
        """Test normalizing string with newlines."""
        string_with_newlines = "line1\nline2\nline3"
        result = self.influx.normalize_value_to_write(string_with_newlines)
        self.assertEqual(result, string_with_newlines)

    def test_normalize_special_unicode(self):
        """Test normalizing special unicode characters."""
        unicode_string = "测试中文字符 テスト 🚀"
        result = self.influx.normalize_value_to_write(unicode_string)
        self.assertEqual(result, unicode_string)


@pytest.mark.unit
class TestDeleteEdgeCases(unittest.TestCase):
    """Test delete method with additional edge cases."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_delete_with_empty_filters(self):
        """Test delete with empty filters dict."""
        self.influx.delete(measurement='cpu', filters={})
        self.mock_client.query.assert_called()

    def test_delete_with_special_characters_in_measurement(self):
        """Test delete with special characters in measurement name."""
        self.influx.delete(measurement='cpu-metrics')
        self.mock_client.query.assert_called()

    def test_delete_with_multiple_filters_and_time(self):
        """Test delete with complex filter combination."""
        self.influx.delete(
            measurement='cpu',
            start_time='2024-01-01T00:00:00Z',
            end_time='2024-12-31T23:59:59Z',
            filters={
                'host': 'server1',
                'region': 'us-west',
                'env': 'prod',
                'datacenter': 'dc1'
            }
        )
        self.mock_client.query.assert_called()


@pytest.mark.unit
class TestConnectionManagement(unittest.TestCase):
    """Test connection and client management."""

    def test_get_client_returns_client_instance(self):
        """Test get_client property returns client."""
        mock_client = create_comprehensive_mock_client()
        influx = InfluxdbOperation(client=mock_client)

        client = influx.get_client
        self.assertIs(client, mock_client)

    def test_get_client_info_contains_all_fields(self):
        """Test get_client_info returns complete info."""
        influx = InfluxdbOperation(
            host='test.host.com',
            port=8086,
            timeout=60
        )

        info = influx.get_client_info

        self.assertEqual(info['host'], 'test.host.com')
        self.assertEqual(info['port'], 8086)
        self.assertEqual(info['timeout'], 60)
        self.assertIn('database', info)
