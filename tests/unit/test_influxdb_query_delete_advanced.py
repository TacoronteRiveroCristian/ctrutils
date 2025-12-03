"""Tests for query, delete, and advanced operations."""
import unittest
import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock
from datetime import datetime
from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from tests.fixtures.influxdb_fixtures import (
    create_comprehensive_mock_client,
    create_mock_query_result,
    create_continuous_queries_response,
)


@pytest.mark.unit
class TestGetDataOperations(unittest.TestCase):
    """Test get_data method."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_get_data_basic(self):
        """Test basic get_data operation."""
        points = [
            {'time': '2024-01-01T12:00:00Z', 'value': 1.0},
            {'time': '2024-01-01T12:01:00Z', 'value': 2.0},
        ]
        self.mock_client.query.return_value = create_mock_query_result(points)

        result = self.influx.get_data('SELECT * FROM cpu')
        self.assertIsNotNone(result)

    def test_get_data_returns_dataframe(self):
        """Test get_data returns DataFrame."""
        points = [
            {'time': '2024-01-01T12:00:00Z', 'value': 1.0},
            {'time': '2024-01-01T12:01:00Z', 'value': 2.0},
        ]
        mock_result = create_mock_query_result(points)
        self.mock_client.query.return_value = mock_result

        result = self.influx.get_data('SELECT * FROM cpu')
        self.assertIsInstance(result, pd.DataFrame)

    def test_get_data_with_database(self):
        """Test get_data with specific database."""
        points = [{'time': f'2024-01-01T12:{i:02d}:00Z', 'value': float(i)} for i in range(10)]
        self.mock_client.query.return_value = create_mock_query_result(points)

        result = self.influx.get_data('SELECT * FROM cpu', database='custom_db')
        self.assertIsNotNone(result)


@pytest.mark.unit
class TestExecuteQueryBuilder(unittest.TestCase):
    """Test execute_query_builder method."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_execute_query_builder_basic(self):
        """Test execute_query_builder basic usage."""
        points = [{'time': '2024-01-01T12:00:00Z', 'value': 1.0}]
        self.mock_client.query.return_value = create_mock_query_result(points)

        result = self.influx.execute_query_builder(
            measurement='cpu',
            fields=['value']
        )
        self.assertIsNotNone(result)

    def test_execute_query_builder_as_dataframe(self):
        """Test execute_query_builder with as_dataframe=True."""
        points = [{'time': '2024-01-01T12:00:00Z', 'value': 1.0}]
        self.mock_client.query.return_value = create_mock_query_result(points)

        result = self.influx.execute_query_builder(
            measurement='cpu',
            fields=['value'],
            as_dataframe=True
        )
        self.assertIsInstance(result, pd.DataFrame)


@pytest.mark.unit
class TestDeleteOperations(unittest.TestCase):
    """Test delete method with various filters."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_delete_with_time_range(self):
        """Test delete with start_time and end_time."""
        self.influx.delete(
            measurement='cpu',
            start_time='2024-01-01T00:00:00Z',
            end_time='2024-01-02T00:00:00Z'
        )
        self.mock_client.query.assert_called()

    def test_delete_with_tag_filters(self):
        """Test delete with tag filters."""
        self.influx.delete(
            measurement='cpu',
            filters={'host': 'server1'}
        )
        self.mock_client.query.assert_called()

    def test_delete_with_combined_filters(self):
        """Test delete with time range and tag filters."""
        self.influx.delete(
            measurement='cpu',
            start_time='2024-01-01T00:00:00Z',
            filters={'host': 'server1'}
        )
        self.mock_client.query.assert_called()

    def test_delete_all_data(self):
        """Test delete all data from measurement."""
        self.influx.delete(measurement='cpu')
        self.mock_client.query.assert_called()


@pytest.mark.unit
class TestCountOperations(unittest.TestCase):
    """Test count_points method."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_count_points_basic(self):
        """Test basic count_points."""
        points = [{'time': '2024-01-01T12:00:00Z', 'count': 10}]
        mock_result = create_mock_query_result(points)
        self.mock_client.query.return_value = mock_result

        count = self.influx.count_points('cpu')
        self.assertIsInstance(count, int)

    def test_count_points_with_time_range(self):
        """Test count_points with time range."""
        points = [{'time': '2024-01-01T12:00:00Z', 'count': 5}]
        mock_result = create_mock_query_result(points)
        self.mock_client.query.return_value = mock_result

        count = self.influx.count_points(
            'cpu',
            start_time='2024-01-01T00:00:00Z',
            end_time='2024-01-02T00:00:00Z'
        )
        self.assertIsInstance(count, int)


@pytest.mark.unit
class TestContinuousQueries(unittest.TestCase):
    """Test continuous query operations."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_list_continuous_queries(self):
        """Test listing continuous queries."""
        mock_result = create_continuous_queries_response()
        self.mock_client.query.return_value = mock_result

        result = self.influx.list_continuous_queries()
        self.assertIsInstance(result, list)

    def test_create_continuous_query(self):
        """Test creating a continuous query."""
        self.influx.create_continuous_query(
            cq_name='cq_1h',
            measurement='cpu',
            target_measurement='cpu_1h',
            aggregation_func='MEAN',
            aggregation_window='1h'
        )
        self.mock_client.query.assert_called()

    def test_drop_continuous_query(self):
        """Test dropping a continuous query."""
        self.influx.drop_continuous_query('cq_1h')
        self.mock_client.query.assert_called()


@pytest.mark.unit
class TestTransactionContextManager(unittest.TestCase):
    """Test transaction context manager."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_transaction_successful(self):
        """Test successful transaction."""
        with self.influx.transaction():
            pass  # Transaction completes successfully

    def test_transaction_with_database_switch(self):
        """Test transaction with database parameter."""
        self.mock_client.get_list_database.return_value = [{'name': 'other_db'}]

        with self.influx.transaction(database='other_db'):
            self.assertEqual(self.influx._database, 'other_db')

    def test_transaction_rollback_on_exception(self):
        """Test transaction rolls back on exception."""
        self.mock_client.get_list_database.return_value = [{'name': 'other_db'}]
        original_db = self.influx._database

        try:
            with self.influx.transaction(database='other_db'):
                raise ValueError("Test error")
        except ValueError:
            pass

        # Database should be restored
        self.assertEqual(self.influx._database, original_db)


