"""Tests for time series and helper methods in InfluxDB operations."""
import unittest
import pytest
from unittest.mock import Mock
from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from tests.fixtures.influxdb_fixtures import create_comprehensive_mock_client


@pytest.mark.unit
class TestBuildQueryFields(unittest.TestCase):
    """Test build_query_fields method."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)

    def test_build_query_fields_with_list(self):
        """Test build_query_fields with list of fields."""
        fields = ['temperature', 'pressure', 'humidity']
        operation = 'MEAN'

        result = self.influx.build_query_fields(fields, operation)

        self.assertIsInstance(result, dict)
        self.assertIn('fields', result)
        self.assertIn('MEAN', result['fields'])
        self.assertIn('temperature', result['fields'])

    def test_build_query_fields_with_dict_integers(self):
        """Test build_query_fields with dict containing integers."""
        fields = {
            'integer': ['count', 'total'],
            'float': ['temperature', 'pressure']
        }
        operation = 'SUM'

        result = self.influx.build_query_fields(fields, operation)

        self.assertIsInstance(result, dict)
        self.assertIn('integer', result)
        self.assertIn('float', result)
        # Integers don't get operation applied
        self.assertNotIn('SUM', result['integer'])
        # Floats get operation applied
        self.assertIn('SUM', result['float'])

    def test_build_query_fields_with_dict_booleans(self):
        """Test build_query_fields with dict containing booleans."""
        fields = {
            'boolean': ['is_active', 'is_online'],
            'float': ['value']
        }
        operation = 'MEAN'

        result = self.influx.build_query_fields(fields, operation)

        self.assertIsInstance(result, dict)
        self.assertIn('boolean', result)
        # Booleans don't get operation applied
        self.assertNotIn('MEAN', result['boolean'])

    def test_build_query_fields_with_dict_mixed_types(self):
        """Test build_query_fields with dict containing mixed types."""
        fields = {
            'integer': ['count'],
            'float': ['temperature', 'pressure'],
            'string': ['status']
        }
        operation = 'MAX'

        result = self.influx.build_query_fields(fields, operation)

        self.assertIsInstance(result, dict)
        self.assertIn('integer', result)
        self.assertIn('float', result)
        self.assertIn('string', result)

    def test_build_query_fields_single_field_list(self):
        """Test build_query_fields with single field in list."""
        fields = ['temperature']
        operation = 'MEAN'

        result = self.influx.build_query_fields(fields, operation)

        self.assertIn('fields', result)
        self.assertIn('temperature', result['fields'])

    def test_build_query_fields_empty_list(self):
        """Test build_query_fields with empty list."""
        fields = []
        operation = 'MEAN'

        result = self.influx.build_query_fields(fields, operation)

        self.assertIsInstance(result, dict)

    def test_build_query_fields_with_mean_operation(self):
        """Test build_query_fields with MEAN operation."""
        fields = ['value1', 'value2']
        operation = 'MEAN'

        result = self.influx.build_query_fields(fields, operation)

        self.assertIn('MEAN', result['fields'])

    def test_build_query_fields_with_sum_operation(self):
        """Test build_query_fields with SUM operation."""
        fields = ['total', 'count']
        operation = 'SUM'

        result = self.influx.build_query_fields(fields, operation)

        self.assertIn('SUM', result['fields'])

    def test_build_query_fields_with_max_operation(self):
        """Test build_query_fields with MAX operation."""
        fields = ['peak_value']
        operation = 'MAX'

        result = self.influx.build_query_fields(fields, operation)

        self.assertIn('MAX', result['fields'])

    def test_build_query_fields_with_min_operation(self):
        """Test build_query_fields with MIN operation."""
        fields = ['min_value']
        operation = 'MIN'

        result = self.influx.build_query_fields(fields, operation)

        self.assertIn('MIN', result['fields'])


@pytest.mark.unit
class TestRetentionPolicies(unittest.TestCase):
    """Test retention policy methods."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_get_retention_policies_returns_list(self):
        """Test get_retention_policies returns list."""
        from tests.fixtures.influxdb_fixtures import create_database_list_response
        self.mock_client.get_list_database.return_value = create_database_list_response(['test_db'])
        self.mock_client.get_list_retention_policies.return_value = []

        result = self.influx.get_retention_policies()

        self.mock_client.get_list_retention_policies.assert_called()
        self.assertIsInstance(result, list)

    def test_get_retention_policies_with_specific_database(self):
        """Test get_retention_policies with specific database parameter."""
        from tests.fixtures.influxdb_fixtures import create_database_list_response
        self.mock_client.get_list_database.return_value = create_database_list_response(['custom_db'])
        self.mock_client.get_list_retention_policies.return_value = []

        result = self.influx.get_retention_policies(database='custom_db')

        self.mock_client.get_list_retention_policies.assert_called_with('custom_db')
        self.assertIsInstance(result, list)


@pytest.mark.unit
class TestCreateDatabase(unittest.TestCase):
    """Test create_database method."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)

    def test_create_database_calls_client(self):
        """Test create_database calls client method."""
        self.influx.create_database('new_db')

        self.mock_client.create_database.assert_called_once_with('new_db')

    def test_create_database_with_different_names(self):
        """Test create_database with various database names."""
        test_names = ['db1', 'test_database', 'prod_metrics']

        for db_name in test_names:
            self.mock_client.reset_mock()
            self.influx.create_database(db_name)
            self.mock_client.create_database.assert_called_once_with(db_name)


@pytest.mark.unit
class TestDropDatabase(unittest.TestCase):
    """Test drop_database method."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)

    def test_drop_database_with_confirm_true(self):
        """Test drop_database with confirm=True."""
        self.influx.drop_database('old_db', confirm=True)

        self.mock_client.drop_database.assert_called_once_with('old_db')

    def test_drop_database_without_confirm_raises(self):
        """Test drop_database without confirm raises ValueError."""
        with pytest.raises(ValueError, match="Debe confirmar"):
            self.influx.drop_database('old_db')

    def test_drop_database_with_confirm_false_raises(self):
        """Test drop_database with confirm=False raises ValueError."""
        with pytest.raises(ValueError, match="Debe confirmar"):
            self.influx.drop_database('old_db', confirm=False)


@pytest.mark.unit
class TestDropMeasurement(unittest.TestCase):
    """Test drop_measurement method."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_drop_measurement_with_confirm_true(self):
        """Test drop_measurement with confirm=True."""
        self.influx.drop_measurement('old_measurement', confirm=True)

        self.mock_client.query.assert_called()

    def test_drop_measurement_without_confirm_raises(self):
        """Test drop_measurement without confirm raises ValueError."""
        with pytest.raises(ValueError, match="Debe confirmar"):
            self.influx.drop_measurement('old_measurement')

    def test_drop_measurement_with_specific_database(self):
        """Test drop_measurement with specific database."""
        self.influx.drop_measurement('old_measurement', database='custom_db', confirm=True)

        self.mock_client.query.assert_called()


@pytest.mark.unit
class TestListTags(unittest.TestCase):
    """Test list_tags method."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_list_tags_returns_list(self):
        """Test list_tags returns list."""
        from tests.fixtures.influxdb_fixtures import create_tag_keys_response

        self.mock_client.query.return_value = create_tag_keys_response(['host', 'region', 'datacenter'])

        result = self.influx.list_tags('cpu')

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)

    def test_list_tags_with_database(self):
        """Test list_tags with specific database."""
        from tests.fixtures.influxdb_fixtures import create_tag_keys_response

        self.mock_client.query.return_value = create_tag_keys_response(['tag1'])

        result = self.influx.list_tags('cpu', database='custom_db')

        self.assertIsInstance(result, list)


@pytest.mark.unit
class TestListFields(unittest.TestCase):
    """Test list_fields method."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_list_fields_returns_dict(self):
        """Test list_fields returns dict."""
        from tests.fixtures.influxdb_fixtures import create_field_keys_response

        self.mock_client.query.return_value = create_field_keys_response([
            ('temperature', 'float'),
            ('humidity', 'float'),
            ('count', 'integer')
        ])

        result = self.influx.list_fields('sensors')

        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 3)

    def test_list_fields_with_database(self):
        """Test list_fields with specific database."""
        from tests.fixtures.influxdb_fixtures import create_field_keys_response

        self.mock_client.query.return_value = create_field_keys_response([('field1', 'float')])

        result = self.influx.list_fields('cpu', database='custom_db')

        self.assertIsInstance(result, dict)


@pytest.mark.unit
class TestListMeasurements(unittest.TestCase):
    """Test list_measurements method."""

    def setUp(self):
        self.mock_client = create_comprehensive_mock_client()
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_list_measurements_returns_list(self):
        """Test list_measurements returns list."""
        from unittest.mock import MagicMock

        mock_result = MagicMock()
        mock_result.raw = {
            'series': [{
                'values': [['cpu'], ['memory'], ['disk']]
            }]
        }
        self.mock_client.query.return_value = mock_result

        result = self.influx.list_measurements()

        self.assertIsInstance(result, list)

    def test_list_measurements_with_database(self):
        """Test list_measurements with specific database."""
        from unittest.mock import MagicMock

        mock_result = MagicMock()
        mock_result.raw = {'series': [{'values': [['cpu']]}]}
        self.mock_client.query.return_value = mock_result

        result = self.influx.list_measurements(database='custom_db')

        self.assertIsInstance(result, list)
