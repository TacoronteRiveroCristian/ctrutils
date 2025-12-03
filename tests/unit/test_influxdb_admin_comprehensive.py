"""Comprehensive tests for InfluxDB administrative operations."""
import unittest
import pytest
from unittest.mock import Mock
from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from tests.fixtures.influxdb_fixtures import (
    create_comprehensive_mock_client,
    create_database_list_response,
    create_measurements_list_response,
    create_tag_keys_response,
    create_field_keys_response,
    create_retention_policies_response,
)


@pytest.mark.unit
class TestDatabaseOperations(unittest.TestCase):
    """Test database management operations."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_create_database(self):
        """Test create_database method."""
        self.influx.create_database('new_db')
        self.mock_client.create_database.assert_called_with('new_db')

    def test_drop_database_with_confirm_true(self):
        """Test drop_database with confirm=True."""
        self.influx.drop_database('old_db', confirm=True)
        self.mock_client.drop_database.assert_called_with('old_db')

    def test_drop_database_with_confirm_false(self):
        """Test drop_database with confirm=False raises error."""
        with pytest.raises(ValueError, match="Debe confirmar"):
            self.influx.drop_database('old_db', confirm=False)

    def test_list_databases(self):
        """Test list_databases method."""
        self.mock_client.get_list_database.return_value = create_database_list_response(['db1', 'db2'])
        result = self.influx.list_databases()
        self.assertEqual(len(result), 2)

    def test_database_exists_true(self):
        """Test database_exists returns True when database exists."""
        self.mock_client.get_list_database.return_value = create_database_list_response(['test_db'])
        result = self.influx.database_exists('test_db')
        self.assertTrue(result)

    def test_database_exists_false(self):
        """Test database_exists returns False when database doesn't exist."""
        self.mock_client.get_list_database.return_value = create_database_list_response(['other_db'])
        result = self.influx.database_exists('test_db')
        self.assertFalse(result)

    def test_switch_database(self):
        """Test switch_database method."""
        self.mock_client.get_list_database.return_value = create_database_list_response(['new_db'])
        self.influx.switch_database('new_db')
        self.assertEqual(self.influx._database, 'new_db')


@pytest.mark.unit
class TestMeasurementOperations(unittest.TestCase):
    """Test measurement management operations."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_list_measurements(self):
        """Test list_measurements method."""
        mock_result = create_measurements_list_response(['cpu', 'memory'])
        self.mock_client.query.return_value = mock_result
        result = self.influx.list_measurements()
        self.assertIn('cpu', result)
        self.assertIn('memory', result)

    def test_measurement_exists_true(self):
        """Test measurement_exists returns True."""
        mock_result = create_measurements_list_response(['cpu'])
        self.mock_client.query.return_value = mock_result
        result = self.influx.measurement_exists('cpu')
        self.assertTrue(result)

    def test_measurement_exists_false(self):
        """Test measurement_exists returns False."""
        mock_result = create_measurements_list_response(['cpu'])
        self.mock_client.query.return_value = mock_result
        result = self.influx.measurement_exists('disk')
        self.assertFalse(result)

    def test_drop_measurement_with_confirm(self):
        """Test drop_measurement with confirm=True."""
        self.influx.drop_measurement('old_measurement', confirm=True)
        self.mock_client.query.assert_called()

    def test_drop_measurement_without_confirm(self):
        """Test drop_measurement with confirm=False raises error."""
        with pytest.raises(ValueError, match="Debe confirmar"):
            self.influx.drop_measurement('old_measurement', confirm=False)


@pytest.mark.unit
class TestTagAndFieldOperations(unittest.TestCase):
    """Test tag and field introspection operations."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_list_tags(self):
        """Test list_tags method."""
        mock_result = create_tag_keys_response(['host', 'region'])
        self.mock_client.query.return_value = mock_result
        result = self.influx.list_tags('cpu')
        self.assertIn('host', result)
        self.assertIn('region', result)

    def test_list_fields(self):
        """Test list_fields method."""
        mock_result = create_field_keys_response([('value', 'float'), ('count', 'integer')])
        self.mock_client.query.return_value = mock_result
        result = self.influx.list_fields('cpu')
        self.assertIn('value', result)
        self.assertIn('count', result)

    def test_get_field_keys_grouped_by_type(self):
        """Test get_field_keys_grouped_by_type method."""
        mock_result = create_field_keys_response([
            ('temp', 'float'),
            ('count', 'integer'),
            ('value', 'float'),
        ])
        self.mock_client.query.return_value = mock_result
        result = self.influx.get_field_keys_grouped_by_type('sensor_data')

        self.assertIn('float', result)
        self.assertIn('integer', result)
        self.assertIn('temp', result['float'])
        self.assertIn('count', result['integer'])


@pytest.mark.unit
class TestQueryBuilder(unittest.TestCase):
    """Test query_builder method."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_query_builder_basic(self):
        """Test basic query_builder."""
        query = self.influx.query_builder(
            measurement='cpu',
            fields=['usage_user', 'usage_system']
        )
        self.assertIn('SELECT', query)
        self.assertIn('cpu', query)

    def test_query_builder_with_where(self):
        """Test query_builder with WHERE clause."""
        query = self.influx.query_builder(
            measurement='cpu',
            fields=['usage'],
            where_conditions={'host': 'server1'}
        )
        self.assertIn('WHERE', query)
        self.assertIn('server1', query)

    def test_query_builder_with_limit(self):
        """Test query_builder with LIMIT."""
        query = self.influx.query_builder(
            measurement='cpu',
            fields=['*'],
            limit=100
        )
        self.assertIn('LIMIT 100', query)

    def test_query_builder_with_order_by(self):
        """Test query_builder with ORDER BY."""
        query = self.influx.query_builder(
            measurement='cpu',
            fields=['*'],
            order_by='time DESC'
        )
        self.assertIn('ORDER BY time DESC', query)


@pytest.mark.unit
class TestConnectionManagement(unittest.TestCase):
    """Test connection and client management."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_get_client_property(self):
        """Test get_client property."""
        client = self.influx.get_client
        self.assertIs(client, self.mock_client)

    def test_get_client_info_property(self):
        """Test get_client_info property."""
        info = self.influx.get_client_info
        self.assertIn('database', info)
