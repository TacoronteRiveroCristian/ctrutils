"""Tests for advanced InfluxDB features and edge cases."""
import unittest
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime
from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from tests.fixtures.influxdb_fixtures import (
    create_comprehensive_mock_client,
    create_mock_query_result,
    create_test_dataframe,
)


@pytest.mark.unit
class TestConvertToUtcIso(unittest.TestCase):
    """Test _convert_to_utc_iso method with various input types."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)

    def test_convert_datetime_to_iso(self):
        """Test converting datetime object to ISO string."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = self.influx._convert_to_utc_iso(dt)
        self.assertIsInstance(result, str)
        self.assertIn('2024', result)

    def test_convert_pandas_timestamp_to_iso(self):
        """Test converting pandas Timestamp to ISO string."""
        ts = pd.Timestamp('2024-01-01 12:00:00')
        result = self.influx._convert_to_utc_iso(ts)
        self.assertIsInstance(result, str)
        self.assertIn('2024', result)

    def test_convert_string_passthrough(self):
        """Test that ISO strings pass through unchanged."""
        iso_str = '2024-01-01T12:00:00Z'
        result = self.influx._convert_to_utc_iso(iso_str)
        self.assertEqual(result, iso_str)


@pytest.mark.unit
class TestLoggingConfiguration(unittest.TestCase):
    """Test logging configuration methods."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)

    def test_enable_logging_default_level(self):
        """Test enabling logging with default level."""
        import logging
        self.influx.enable_logging()
        self.assertTrue(self.influx._logger.level in [logging.INFO, logging.DEBUG])

    def test_enable_logging_custom_level(self):
        """Test enabling logging with custom level."""
        import logging
        self.influx.enable_logging(level=logging.WARNING)
        self.assertEqual(self.influx._logger.level, logging.WARNING)

    def test_enable_logging_debug(self):
        """Test enabling debug logging."""
        import logging
        self.influx.enable_logging(level=logging.DEBUG)
        self.assertEqual(self.influx._logger.level, logging.DEBUG)


@pytest.mark.unit
class TestDataframeConversion(unittest.TestCase):
    """Test DataFrame conversion and processing."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_get_data_returns_dataframe_with_data(self):
        """Test that get_data returns populated DataFrame."""
        points = [
            {'time': '2024-01-01T12:00:00Z', 'value': 1.0, 'host': 'server1'},
            {'time': '2024-01-01T12:01:00Z', 'value': 2.0, 'host': 'server1'},
            {'time': '2024-01-01T12:02:00Z', 'value': 3.0, 'host': 'server2'},
        ]
        mock_result = create_mock_query_result(points)
        self.mock_client.query.return_value = mock_result

        df = self.influx.get_data('SELECT * FROM cpu')

        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)

    def test_get_data_with_different_fields(self):
        """Test get_data with different field types."""
        points = [
            {'time': '2024-01-01T12:00:00Z', 'temperature': 25.5, 'humidity': 60},
        ]
        mock_result = create_mock_query_result(points)
        self.mock_client.query.return_value = mock_result

        df = self.influx.get_data('SELECT temperature, humidity FROM sensors')

        self.assertIsInstance(df, pd.DataFrame)


@pytest.mark.unit
class TestDeleteAdvancedFilters(unittest.TestCase):
    """Test delete method with complex filter combinations."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_delete_with_multiple_tag_filters(self):
        """Test delete with multiple tag filters."""
        self.influx.delete(
            measurement='cpu',
            filters={'host': 'server1', 'region': 'us-west'}
        )
        self.mock_client.query.assert_called()

    def test_delete_with_time_and_multiple_tags(self):
        """Test delete with time range and multiple tags."""
        self.influx.delete(
            measurement='cpu',
            start_time='2024-01-01T00:00:00Z',
            end_time='2024-01-02T00:00:00Z',
            filters={'host': 'server1', 'region': 'us-west', 'env': 'prod'}
        )
        self.mock_client.query.assert_called()

    def test_delete_only_start_time(self):
        """Test delete with only start time."""
        self.influx.delete(
            measurement='cpu',
            start_time='2024-01-01T00:00:00Z'
        )
        self.mock_client.query.assert_called()

    def test_delete_only_end_time(self):
        """Test delete with only end time."""
        self.influx.delete(
            measurement='cpu',
            end_time='2024-01-02T00:00:00Z'
        )
        self.mock_client.query.assert_called()


@pytest.mark.unit
class TestWriteDataframeEdgeCases(unittest.TestCase):
    """Test write_dataframe with additional edge cases."""

    def setUp(self):
        from tests.fixtures.influxdb_fixtures import create_mock_influxdb_client
        self.mock_client = create_mock_influxdb_client(write_points_return=True)
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_write_dataframe_with_tags_parameter(self):
        """Test write_dataframe with global tags."""
        df = pd.DataFrame({
            'value': [1.0, 2.0, 3.0],
        }, index=pd.date_range('2024-01-01', periods=3, freq='1min'))

        self.influx.write_dataframe(
            measurement='test',
            data=df,
            tags={'env': 'production', 'datacenter': 'us-west'}
        )
        self.assertTrue(self.mock_client.write_points.called)

    def test_write_dataframe_all_numeric_types(self):
        """Test write_dataframe with various numeric types."""
        df = pd.DataFrame({
            'int_val': [1, 2, 3],
            'float_val': [1.1, 2.2, 3.3],
            'np_int': np.array([10, 20, 30], dtype=np.int64),
            'np_float': np.array([1.5, 2.5, 3.5], dtype=np.float64),
        }, index=pd.date_range('2024-01-01', periods=3, freq='1min'))

        result = self.influx.write_dataframe(
            measurement='test',
            data=df,
            validate_data=False
        )
        self.assertIn('written_points', result)

    def test_write_dataframe_with_batch_size_1(self):
        """Test write_dataframe with batch_size=1."""
        df = pd.DataFrame({
            'value': [1.0, 2.0, 3.0],
        }, index=pd.date_range('2024-01-01', periods=3, freq='1min'))

        result = self.influx.write_dataframe(
            measurement='test',
            data=df,
            batch_size=1
        )
        self.assertEqual(result['batches'], 3)


@pytest.mark.unit
class TestQueryBuilderEdgeCases(unittest.TestCase):
    """Test query_builder with edge cases."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_query_builder_single_field(self):
        """Test query_builder with single field."""
        query = self.influx.query_builder(
            measurement='cpu',
            fields=['usage']
        )
        self.assertIn('usage', query)

    def test_query_builder_multiple_fields(self):
        """Test query_builder with multiple fields."""
        query = self.influx.query_builder(
            measurement='cpu',
            fields=['usage_user', 'usage_system', 'usage_idle']
        )
        self.assertIn('usage_user', query)
        self.assertIn('usage_system', query)
        self.assertIn('usage_idle', query)

    def test_query_builder_with_multiple_group_by(self):
        """Test query_builder with multiple GROUP BY fields."""
        query = self.influx.query_builder(
            measurement='cpu',
            fields=['mean(usage)'],
            group_by=['host', 'region', 'datacenter']
        )
        self.assertIn('GROUP BY', query)

    def test_query_builder_complex_where(self):
        """Test query_builder with complex WHERE conditions."""
        query = self.influx.query_builder(
            measurement='cpu',
            fields=['usage'],
            where_conditions={
                'host': 'server1',
                'region': 'us-west',
                'env': 'production'
            }
        )
        self.assertIn('WHERE', query)


@pytest.mark.unit
class TestSwitchDatabaseEdgeCases(unittest.TestCase):
    """Test switch_database with edge cases."""

    def setUp(self):
        from tests.fixtures.influxdb_fixtures import create_database_list_response
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)

    def test_switch_database_creates_if_not_exists(self):
        """Test switch_database creates database if it doesn't exist."""
        from tests.fixtures.influxdb_fixtures import create_database_list_response

        # First call: database doesn't exist
        # Second call: database exists after creation
        self.mock_client.get_list_database.side_effect = [
            create_database_list_response(['other_db']),
            create_database_list_response(['other_db', 'new_db']),
        ]

        self.influx.switch_database('new_db')

        self.mock_client.create_database.assert_called_with('new_db')
        self.assertEqual(self.influx._database, 'new_db')

    def test_switch_database_updates_internal_state(self):
        """Test switch_database updates internal database state."""
        from tests.fixtures.influxdb_fixtures import create_database_list_response

        self.mock_client.get_list_database.return_value = create_database_list_response(['existing_db'])
        self.influx._database = 'old_db'

        self.influx.switch_database('existing_db')

        self.assertEqual(self.influx._database, 'existing_db')
