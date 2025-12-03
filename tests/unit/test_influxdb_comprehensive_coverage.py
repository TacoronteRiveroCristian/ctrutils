"""Comprehensive tests to increase coverage of remaining uncovered lines."""
import unittest
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from influxdb.exceptions import InfluxDBClientError
from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from tests.fixtures.influxdb_fixtures import (
    create_comprehensive_mock_client,
    create_mock_query_result,
    create_database_list_response,
)


@pytest.mark.unit
class TestSwitchDatabaseWithCreation(unittest.TestCase):
    """Test switch_database when database needs to be created."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)

    def test_switch_database_creates_and_switches(self):
        """Test switch_database creates database if it doesn't exist."""
        # First call: database doesn't exist yet
        # Second call: database exists after creation
        self.mock_client.get_list_database.side_effect = [
            create_database_list_response(['existing_db']),
            create_database_list_response(['existing_db', 'new_db']),
        ]

        self.influx.switch_database('new_db')

        # Verify database was created
        self.mock_client.create_database.assert_called_once_with('new_db')
        # Verify internal state was updated
        self.assertEqual(self.influx._database, 'new_db')


@pytest.mark.unit
class TestWriteDataframeWithBooleanConversion(unittest.TestCase):
    """Test write_dataframe with boolean to float conversion."""

    def setUp(self):
        from tests.fixtures.influxdb_fixtures import create_mock_influxdb_client
        self.mock_client = create_mock_influxdb_client(write_points_return=True)
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_write_dataframe_convert_bool_with_custom_suffix(self):
        """Test boolean conversion with custom suffix."""
        df = pd.DataFrame({
            'is_active': [True, False, True],
            'is_online': [False, True, False],
        }, index=pd.date_range('2024-01-01', periods=3, freq='1min'))

        result = self.influx.write_dataframe(
            measurement='status',
            data=df,
            convert_bool_to_float=True,
            suffix_bool_to_float='_bool'
        )

        self.assertTrue(self.mock_client.write_points.called)
        self.assertGreater(result['written_points'], 0)

    def test_write_dataframe_with_pass_to_float(self):
        """Test write_dataframe with pass_to_float parameter."""
        df = pd.DataFrame({
            'count': [1, 2, 3],  # Integers
            'value': [1.5, 2.5, 3.5],  # Floats
        }, index=pd.date_range('2024-01-01', periods=3, freq='1min'))

        result = self.influx.write_dataframe(
            measurement='metrics',
            data=df,
            pass_to_float=True,
            validate_data=False
        )

        self.assertGreater(result['written_points'], 0)


@pytest.mark.unit
class TestListContinuousQueries(unittest.TestCase):
    """Test listing continuous queries."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_list_continuous_queries_with_results(self):
        """Test list_continuous_queries returns query list."""
        mock_result = MagicMock()
        mock_result.raw = {
            'series': [{
                'name': 'test_db',
                'columns': ['name', 'query'],
                'values': [
                    ['cq_1h', 'CREATE CONTINUOUS QUERY cq_1h ...'],
                    ['cq_daily', 'CREATE CONTINUOUS QUERY cq_daily ...'],
                ]
            }]
        }
        self.mock_client.query.return_value = mock_result

        result = self.influx.list_continuous_queries()

        self.assertIsInstance(result, list)

    def test_list_continuous_queries_empty(self):
        """Test list_continuous_queries with no CQs."""
        mock_result = MagicMock()
        mock_result.raw = {'series': []}
        self.mock_client.query.return_value = mock_result

        result = self.influx.list_continuous_queries()

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)


@pytest.mark.unit
class TestDropContinuousQuery(unittest.TestCase):
    """Test dropping continuous queries."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_drop_continuous_query(self):
        """Test dropping a continuous query."""
        self.influx.drop_continuous_query('cq_test')

        self.mock_client.query.assert_called()
        call_args = str(self.mock_client.query.call_args)
        self.assertIn('DROP CONTINUOUS QUERY', call_args)


@pytest.mark.unit
class TestListTagValues(unittest.TestCase):
    """Test listing tag values for measurements."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_list_tag_values_returns_list(self):
        """Test list_tag_values returns list of values."""
        mock_result = MagicMock()
        mock_result.raw = {
            'series': [{
                'values': [['value1'], ['value2'], ['value3']]
            }]
        }
        self.mock_client.query.return_value = mock_result

        result = self.influx.list_tag_values('cpu', 'host')

        self.assertIsInstance(result, list)

    def test_list_tag_values_empty(self):
        """Test list_tag_values with no values."""
        mock_result = MagicMock()
        mock_result.raw = {'series': []}
        self.mock_client.query.return_value = mock_result

        result = self.influx.list_tag_values('cpu', 'host')

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)


@pytest.mark.unit
class TestCountPoints(unittest.TestCase):
    """Test count_points method with various scenarios."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_count_points_with_database_parameter(self):
        """Test count_points with specific database."""
        mock_result = MagicMock()
        mock_result.raw = {'series': [{'values': [[100]]}]}
        self.mock_client.query.return_value = mock_result

        count = self.influx.count_points('cpu', database='custom_db')

        self.assertIsInstance(count, int)
        self.mock_client.query.assert_called()


@pytest.mark.unit
class TestTransactionContextManager(unittest.TestCase):
    """Test transaction context manager functionality."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'original_db'

    def test_transaction_context_preserves_database(self):
        """Test transaction context preserves original database."""
        original_db = self.influx._database

        with self.influx.transaction(database='temp_db'):
            # Inside context, database should be temp_db
            self.assertEqual(self.influx._database, 'temp_db')

        # After context, should be restored
        self.assertEqual(self.influx._database, original_db)

    def test_transaction_context_with_operations(self):
        """Test transaction context with write operations."""
        with self.influx.transaction(database='test_db'):
            points = [{
                'measurement': 'test',
                'time': '2024-01-01T12:00:00Z',
                'fields': {'value': 1.0}
            }]
            result = self.influx.write_points(points)

        self.assertIn('written_points', result)


@pytest.mark.unit
class TestDatabaseExists(unittest.TestCase):
    """Test database_exists method."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)

    def test_database_exists_true(self):
        """Test database_exists returns True when database exists."""
        self.mock_client.get_list_database.return_value = create_database_list_response(
            ['db1', 'db2', 'test_db']
        )

        exists = self.influx.database_exists('test_db')

        self.assertTrue(exists)

    def test_database_exists_false(self):
        """Test database_exists returns False when database doesn't exist."""
        self.mock_client.get_list_database.return_value = create_database_list_response(
            ['db1', 'db2']
        )

        exists = self.influx.database_exists('test_db')

        self.assertFalse(exists)


@pytest.mark.unit
class TestListDatabases(unittest.TestCase):
    """Test list_databases method."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)

    def test_list_databases_returns_list(self):
        """Test list_databases returns list of database names."""
        self.mock_client.get_list_database.return_value = create_database_list_response(
            ['db1', 'db2', 'db3', 'test_db']
        )

        databases = self.influx.list_databases()

        self.assertIsInstance(databases, list)
        self.assertEqual(len(databases), 4)
        self.assertIn('test_db', databases)

    def test_list_databases_empty(self):
        """Test list_databases with no databases."""
        self.mock_client.get_list_database.return_value = create_database_list_response([])

        databases = self.influx.list_databases()

        self.assertIsInstance(databases, list)
        self.assertEqual(len(databases), 0)
