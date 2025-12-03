"""Tests for retention policies and helper methods."""
import unittest
import pytest
from unittest.mock import Mock, MagicMock
from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from tests.fixtures.influxdb_fixtures import (
    create_comprehensive_mock_client,
    create_retention_policies_response,
)


@pytest.mark.unit
class TestQueryBuilderAdvanced(unittest.TestCase):
    """Test advanced query_builder scenarios."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_query_builder_with_group_by(self):
        """Test query_builder with GROUP BY."""
        query = self.influx.query_builder(
            measurement='cpu',
            fields=['mean(usage)'],
            group_by=['host']
        )
        self.assertIn('GROUP BY', query)
        self.assertIn('host', query)

    def test_query_builder_all_parameters(self):
        """Test query_builder with all parameters."""
        query = self.influx.query_builder(
            measurement='cpu',
            fields=['usage'],
            where_conditions={'host': 'server1'},
            group_by=['region'],
            order_by='time ASC',
            limit=1000
        )
        self.assertIn('SELECT', query)
        self.assertIn('WHERE', query)
        self.assertIn('GROUP BY', query)
        self.assertIn('ORDER BY', query)
        self.assertIn('LIMIT', query)

    def test_query_builder_no_fields(self):
        """Test query_builder with no fields (SELECT *)."""
        query = self.influx.query_builder(measurement='cpu')
        self.assertIn('SELECT *', query)


@pytest.mark.unit
class TestHelperMethods(unittest.TestCase):
    """Test helper and utility methods."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_get_client_property(self):
        """Test get_client property returns the client."""
        client = self.influx.get_client
        self.assertIs(client, self.mock_client)

    def test_get_client_info(self):
        """Test get_client_info returns configuration."""
        info = self.influx.get_client_info
        self.assertIn('host', info)
        self.assertIn('port', info)
        self.assertIn('database', info)


@pytest.mark.unit
class TestExecuteQueryBuilderAdvanced(unittest.TestCase):
    """Test execute_query_builder with various scenarios."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_execute_query_builder_with_group_by(self):
        """Test execute_query_builder with GROUP BY."""
        from tests.fixtures.influxdb_fixtures import create_mock_query_result

        points = [
            {'time': '2024-01-01T12:00:00Z', 'host': 'server1', 'mean': 50.0},
        ]
        self.mock_client.query.return_value = create_mock_query_result(points)

        result = self.influx.execute_query_builder(
            measurement='cpu',
            fields=['mean(usage)'],
            group_by=['host']
        )
        self.assertIsNotNone(result)

    def test_execute_query_builder_with_where_conditions(self):
        """Test execute_query_builder with WHERE conditions."""
        from tests.fixtures.influxdb_fixtures import create_mock_query_result

        points = [
            {'time': '2024-01-01T12:00:00Z', 'value': 1.0},
        ]
        self.mock_client.query.return_value = create_mock_query_result(points)

        result = self.influx.execute_query_builder(
            measurement='cpu',
            fields=['usage'],
            where_conditions={'region': 'us-west'}
        )
        self.assertIsNotNone(result)

    def test_execute_query_builder_with_limit(self):
        """Test execute_query_builder with LIMIT."""
        from tests.fixtures.influxdb_fixtures import create_mock_query_result

        points = [
            {'time': f'2024-01-01T12:{i:02d}:00Z', 'value': float(i)}
            for i in range(5)
        ]
        self.mock_client.query.return_value = create_mock_query_result(points)

        result = self.influx.execute_query_builder(
            measurement='cpu',
            fields=['*'],
            limit=100
        )
        self.assertIsNotNone(result)


@pytest.mark.unit
class TestTagValueOperations(unittest.TestCase):
    """Test tag value listing operations."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_list_tag_values(self):
        """Test listing values for a specific tag."""
        mock_result = MagicMock()
        mock_result.raw = {
            'series': [{
                'values': [['server1'], ['server2'], ['server3']]
            }]
        }
        self.mock_client.query.return_value = mock_result

        result = self.influx.list_tag_values('cpu', 'host')
        self.assertIsInstance(result, list)

    def test_list_tag_values_with_database(self):
        """Test listing tag values with specific database."""
        mock_result = MagicMock()
        mock_result.raw = {
            'series': [{
                'values': [['us-west'], ['us-east']]
            }]
        }
        self.mock_client.query.return_value = mock_result

        result = self.influx.list_tag_values('cpu', 'region', database='custom_db')
        self.assertIsInstance(result, list)


