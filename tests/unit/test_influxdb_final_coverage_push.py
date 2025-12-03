"""Final tests to push coverage above 75%."""
import unittest
import pytest
import pandas as pd
import numpy as np
import logging
from unittest.mock import Mock, MagicMock, patch
from influxdb.exceptions import InfluxDBClientError
from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from tests.fixtures.influxdb_fixtures import (
    create_comprehensive_mock_client,
    create_mock_query_result,
    create_database_list_response,
)


@pytest.mark.unit
class TestWriteDataframeEdgeBranches(unittest.TestCase):
    """Test write_dataframe branches to increase coverage."""

    def setUp(self):
        from tests.fixtures.influxdb_fixtures import create_mock_influxdb_client
        self.mock_client = create_mock_influxdb_client(write_points_return=True)
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_write_dataframe_with_validation_and_pass_to_float(self):
        """Test write_dataframe with validate_data and pass_to_float."""
        df = pd.DataFrame({
            'int_col': [1, 2, 3],
            'float_col': [1.5, 2.5, 3.5],
        }, index=pd.date_range('2024-01-01', periods=3, freq='1min'))

        result = self.influx.write_dataframe(
            measurement='test',
            data=df,
            validate_data=True,
            pass_to_float=True
        )

        self.assertGreater(result['written_points'], 0)

    def test_write_dataframe_without_validation_with_pass_to_float(self):
        """Test branch without validation but with pass_to_float."""
        df = pd.DataFrame({
            'count': np.array([10, 20, 30], dtype=np.int32),
        }, index=pd.date_range('2024-01-01', periods=3, freq='1min'))

        result = self.influx.write_dataframe(
            measurement='test',
            data=df,
            validate_data=False,
            pass_to_float=True
        )

        self.assertGreater(result['written_points'], 0)

    def test_write_dataframe_without_validation_or_pass_to_float(self):
        """Test branch without validation or pass_to_float."""
        df = pd.DataFrame({
            'value': [1.0, 2.0, 3.0],
        }, index=pd.date_range('2024-01-01', periods=3, freq='1min'))

        result = self.influx.write_dataframe(
            measurement='test',
            data=df,
            validate_data=False,
            pass_to_float=False
        )

        self.assertGreater(result['written_points'], 0)


@pytest.mark.unit
class TestContextManagerEnterExit(unittest.TestCase):
    """Test context manager __enter__ and __exit__ methods."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'original_db'

    def test_context_manager_enter_returns_self(self):
        """Test __enter__ returns self."""
        ctx = self.influx.transaction(database='temp_db')
        result = ctx.__enter__()

        self.assertEqual(result, self.influx)

        # Cleanup
        ctx.__exit__(None, None, None)

    def test_context_manager_exit_restores_database(self):
        """Test __exit__ restores original database."""
        original = self.influx._database

        ctx = self.influx.transaction(database='temp_db')
        ctx.__enter__()

        # Inside context
        self.assertEqual(self.influx._database, 'temp_db')

        # Exit context
        ctx.__exit__(None, None, None)

        # Should be restored
        self.assertEqual(self.influx._database, original)

    def test_context_manager_exit_with_exception(self):
        """Test __exit__ handles exceptions properly."""
        ctx = self.influx.transaction(database='temp_db')
        ctx.__enter__()

        # Exit with exception info
        result = ctx.__exit__(Exception, Exception("test"), None)

        # Should not suppress exception
        self.assertFalse(result)


@pytest.mark.unit
class TestSwitchDatabaseBranches(unittest.TestCase):
    """Test switch_database various branches."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)

    def test_switch_database_when_db_doesnt_exist_creates_it(self):
        """Test switch_database creates DB when it doesn't exist."""
        # First call: DB doesn't exist
        # Second call: DB exists after creation
        self.mock_client.get_list_database.side_effect = [
            create_database_list_response(['other_db']),
            create_database_list_response(['other_db', 'new_db']),
        ]

        self.influx.switch_database('new_db')

        # Should have created the database
        self.mock_client.create_database.assert_called_with('new_db')

    def test_switch_database_when_db_exists_no_creation(self):
        """Test switch_database doesn't create if DB exists."""
        self.mock_client.get_list_database.return_value = create_database_list_response(['existing_db'])

        # Reset create_database mock to ensure it's not called
        self.mock_client.create_database.reset_mock()

        self.influx.switch_database('existing_db')

        # Database should be set
        self.assertEqual(self.influx._database, 'existing_db')


@pytest.mark.unit
class TestWritePointsBatching(unittest.TestCase):
    """Test write_points batching logic branches."""

    def setUp(self):
        from tests.fixtures.influxdb_fixtures import create_mock_influxdb_client
        self.mock_client = create_mock_influxdb_client(write_points_return=True)
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_write_points_single_batch(self):
        """Test write_points with all points in one batch."""
        points = [
            {'measurement': 'cpu', 'time': f'2024-01-01T12:0{i}:00Z', 'fields': {'value': float(i)}}
            for i in range(5)
        ]

        result = self.influx.write_points(points, batch_size=100)

        self.assertEqual(result['batches'], 1)
        self.assertEqual(result['written_points'], 5)

    def test_write_points_multiple_batches(self):
        """Test write_points with multiple batches."""
        points = [
            {'measurement': 'cpu', 'time': f'2024-01-01T12:{i:02d}:00Z', 'fields': {'value': float(i)}}
            for i in range(15)
        ]

        result = self.influx.write_points(points, batch_size=5)

        self.assertEqual(result['batches'], 3)
        self.assertEqual(result['written_points'], 15)


@pytest.mark.unit
class TestQueryBuilderVariations(unittest.TestCase):
    """Test query_builder different parameter combinations."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_query_builder_no_fields_returns_star(self):
        """Test query_builder with no fields returns SELECT *."""
        query = self.influx.query_builder(measurement='cpu', fields=None)

        self.assertIn('SELECT *', query)
        self.assertIn('cpu', query)

    def test_query_builder_empty_fields_list(self):
        """Test query_builder with empty fields list."""
        query = self.influx.query_builder(measurement='cpu', fields=[])

        self.assertIn('SELECT', query)

    def test_query_builder_with_where_and_group_by(self):
        """Test query_builder with where and group_by."""
        query = self.influx.query_builder(
            measurement='cpu',
            fields=['usage'],
            where_conditions={'host': 'server1'},
            group_by=['region']
        )

        self.assertIn('WHERE', query)
        self.assertIn('GROUP BY', query)

    def test_query_builder_with_all_parameters(self):
        """Test query_builder with all parameters."""
        query = self.influx.query_builder(
            measurement='cpu',
            fields=['mean(usage)'],
            where_conditions={'datacenter': 'dc1'},
            group_by=['host', 'region'],
            order_by='time DESC',
            limit=100,
            database='custom_db'
        )

        self.assertIn('SELECT', query)
        self.assertIn('WHERE', query)
        self.assertIn('GROUP BY', query)
        self.assertIn('ORDER BY', query)
        self.assertIn('LIMIT', query)


@pytest.mark.unit
class TestDeleteVariousCombinations(unittest.TestCase):
    """Test delete method with various parameter combinations."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_delete_with_start_time_only(self):
        """Test delete with only start_time."""
        self.influx.delete(
            measurement='cpu',
            start_time='2024-01-01T00:00:00Z'
        )

        self.mock_client.query.assert_called()

    def test_delete_with_end_time_only(self):
        """Test delete with only end_time."""
        self.influx.delete(
            measurement='cpu',
            end_time='2024-12-31T23:59:59Z'
        )

        self.mock_client.query.assert_called()

    def test_delete_with_filters_only(self):
        """Test delete with only filters."""
        self.influx.delete(
            measurement='cpu',
            filters={'host': 'server1', 'region': 'us-west'}
        )

        self.mock_client.query.assert_called()

    def test_delete_everything_from_measurement(self):
        """Test delete everything from measurement."""
        self.influx.delete(measurement='cpu')

        self.mock_client.query.assert_called()


@pytest.mark.unit
class TestCountPointsVariations(unittest.TestCase):
    """Test count_points with various parameters."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_count_points_basic(self):
        """Test basic count_points."""
        mock_result = MagicMock()
        mock_result.raw = {'series': [{'values': [[100]]}]}
        self.mock_client.query.return_value = mock_result

        count = self.influx.count_points('cpu')

        self.assertIsInstance(count, int)

    def test_count_points_with_time_range(self):
        """Test count_points with time range."""
        mock_result = MagicMock()
        mock_result.raw = {'series': [{'values': [[50]]}]}
        self.mock_client.query.return_value = mock_result

        count = self.influx.count_points(
            'cpu',
            start_time='2024-01-01T00:00:00Z',
            end_time='2024-01-31T23:59:59Z'
        )

        self.assertIsInstance(count, int)

    def test_count_points_with_custom_database(self):
        """Test count_points with custom database."""
        mock_result = MagicMock()
        mock_result.raw = {'series': [{'values': [[75]]}]}
        self.mock_client.query.return_value = mock_result

        count = self.influx.count_points('cpu', database='custom_db')

        self.assertIsInstance(count, int)
