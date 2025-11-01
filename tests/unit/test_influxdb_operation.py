"""Tests unitarios para InfluxdbOperation."""
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone
import pandas as pd
import numpy as np

from ctrutils.database.influxdb import InfluxdbOperation


class TestInfluxdbOperationInit(unittest.TestCase):
    """Tests para inicializacion de InfluxdbOperation."""

    @patch('influxdb.InfluxDBClient')
    def test_init_with_all_params(self, mock_client):
        """Test inicializacion con todos los parametros."""
        # Configurar mock para retornar un objeto con atributos necesarios
        mock_instance = Mock()
        mock_client.return_value = mock_instance

        op = InfluxdbOperation(
            host='localhost',
            port=8086,
            username='user',
            password='pass',
            ssl=True,
            verify_ssl=True
        )

        self.assertEqual(op.host, 'localhost')
        self.assertEqual(op.port, 8086)
        self.assertIsNone(op._database)  # database se establece con switch_database()
        # Verificar que el cliente fue creado
        self.assertIsNotNone(op._client)

    @patch('influxdb.InfluxDBClient')
    def test_init_without_database(self, mock_client):
        """Test inicializacion sin base de datos."""
        op = InfluxdbOperation(host='localhost', port=8086)
        self.assertIsNone(op._database)


class TestInfluxdbOperationDataValidation(unittest.TestCase):
    """Tests para validacion de datos."""

    @patch('influxdb.InfluxDBClient')
    def setUp(self, mock_client):
        """Setup para cada test."""
        self.op = InfluxdbOperation(host='localhost', port=8086)
        self.mock_client = mock_client

    def test_validate_point_with_valid_data(self):
        """Test validacion de punto con datos validos."""
        point = {
            'measurement': 'temperature',
            'time': '2024-01-01T12:00:00Z',
            'fields': {'value': 25.5}
        }
        result = self.op._validate_point(point)
        self.assertIsNotNone(result)
        self.assertEqual(result['fields']['value'], 25.5)

    def test_validate_point_with_nan(self):
        """Test validacion de punto con NaN."""
        point = {
            'measurement': 'temperature',
            'time': '2024-01-01T12:00:00Z',
            'fields': {'value': np.nan}
        }
        result = self.op._validate_point(point)
        self.assertIsNone(result)  # Sin campos validos

    def test_validate_point_with_none(self):
        """Test validacion con None."""
        point = {
            'measurement': 'temperature',
            'time': '2024-01-01T12:00:00Z',
            'fields': {'value': None}
        }
        result = self.op._validate_point(point)
        self.assertIsNone(result)  # Sin campos validos

    def test_validate_point_with_mixed_data(self):
        """Test validacion con datos mezclados (validos e invalidos)."""
        point = {
            'measurement': 'temperature',
            'time': '2024-01-01T12:00:00Z',
            'fields': {
                'valid': 42.5,
                'invalid_nan': np.nan,
                'invalid_none': None,
                'valid_string': "test"
            }
        }
        result = self.op._validate_point(point)
        self.assertIsNotNone(result)
        self.assertIn('valid', result['fields'])
        self.assertIn('valid_string', result['fields'])
        self.assertNotIn('invalid_nan', result['fields'])
        self.assertNotIn('invalid_none', result['fields'])


class TestInfluxdbOperationDateConversion(unittest.TestCase):
    """Tests para conversion de fechas."""

    @patch('influxdb.InfluxDBClient')
    def setUp(self, mock_client):
        """Setup para cada test."""
        self.op = InfluxdbOperation(host='localhost', port=8086)

    def test_convert_to_utc_iso_with_datetime(self):
        """Test conversion de datetime a UTC ISO."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = self.op._convert_to_utc_iso(dt)
        # El formato real incluye microsegundos y termina en Z
        self.assertEqual(result, '2024-01-01T12:00:00.000000Z')

    def test_convert_to_utc_iso_with_pandas_timestamp(self):
        """Test conversion de pandas Timestamp."""
        ts = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        result = self.op._convert_to_utc_iso(ts)
        self.assertIn('2024-01-01', result)

    def test_convert_to_utc_iso_with_string(self):
        """Test conversion con string."""
        result = self.op._convert_to_utc_iso('2024-01-01T12:00:00Z')
        self.assertIn('2024-01-01', result)


class TestInfluxdbOperationMetrics(unittest.TestCase):
    """Tests para sistema de metricas."""

    @patch('influxdb.InfluxDBClient')
    def setUp(self, mock_client):
        """Setup para cada test."""
        self.op = InfluxdbOperation(host='localhost', port=8086)

    def test_get_metrics_initial_state(self):
        """Test metricas en estado inicial."""
        metrics = self.op.get_metrics()

        self.assertEqual(metrics['total_writes'], 0)
        self.assertEqual(metrics['total_points'], 0)
        self.assertEqual(metrics['failed_writes'], 0)
        self.assertGreaterEqual(metrics['total_write_time'], 0)

    def test_reset_metrics(self):
        """Test reset de metricas."""
        # Modificar metricas
        self.op._metrics['total_writes'] = 10
        self.op._metrics['total_points'] = 100

        # Reset
        self.op.reset_metrics()

        metrics = self.op.get_metrics()
        self.assertEqual(metrics['total_writes'], 0)
        self.assertEqual(metrics['total_points'], 0)


class TestInfluxdbOperationLogging(unittest.TestCase):
    """Tests para sistema de logging."""

    @patch('influxdb.InfluxDBClient')
    def setUp(self, mock_client):
        """Setup para cada test."""
        self.op = InfluxdbOperation(host='localhost', port=8086)

    def test_enable_logging_default(self):
        """Test activar logging con configuracion por defecto."""
        self.op.enable_logging()
        self.assertIsNotNone(self.op._logger)

    def test_enable_logging_custom_level(self):
        """Test activar logging con nivel personalizado."""
        import logging
        self.op.enable_logging(level=logging.DEBUG)
        self.assertIsNotNone(self.op._logger)
        self.assertEqual(self.op._logger.level, logging.DEBUG)


class TestInfluxdbOperationQueryBuilder(unittest.TestCase):
    """Tests para query builder."""

    @patch('influxdb.InfluxDBClient')
    def setUp(self, mock_client):
        """Setup para cada test."""
        self.op = InfluxdbOperation(host='localhost', port=8086)

    def test_query_builder_simple(self):
        """Test query builder simple."""
        query = self.op.query_builder(measurement='temperature')
        self.assertEqual(query, 'SELECT * FROM "temperature" ORDER BY time DESC')

    def test_query_builder_with_fields(self):
        """Test query builder con campos especificos."""
        query = self.op.query_builder(
            measurement='temperature',
            fields=['value', 'sensor_id']
        )
        self.assertEqual(query, 'SELECT value, sensor_id FROM "temperature" ORDER BY time DESC')

    def test_query_builder_with_where(self):
        """Test query builder con condiciones WHERE."""
        query = self.op.query_builder(
            measurement='temperature',
            where_conditions={'location': 'room_1'}
        )
        self.assertIn('WHERE', query)
        self.assertIn('"location" = \'room_1\'', query)

    def test_query_builder_with_limit(self):
        """Test query builder con LIMIT."""
        query = self.op.query_builder(
            measurement='temperature',
            limit=100
        )
        self.assertIn('LIMIT 100', query)

    def test_query_builder_with_group_by(self):
        """Test query builder con GROUP BY."""
        query = self.op.query_builder(
            measurement='temperature',
            group_by=['location', 'sensor_id']
        )
        self.assertIn('GROUP BY', query)

    def test_query_builder_complex(self):
        """Test query builder complejo."""
        query = self.op.query_builder(
            measurement='temperature',
            fields=['MEAN(value)'],
            where_conditions={'location': 'room_1'},
            group_by=['time(1h)'],
            order_by='time DESC',
            limit=10
        )
        self.assertIn('SELECT MEAN(value)', query)
        self.assertIn('WHERE', query)
        self.assertIn('GROUP BY', query)
        self.assertIn('ORDER BY', query)
        self.assertIn('LIMIT', query)


class TestInfluxdbOperationRetry(unittest.TestCase):
    """Tests para logica de retry."""

    @patch('influxdb.InfluxDBClient')
    def setUp(self, mock_client):
        """Setup para cada test."""
        self.op = InfluxdbOperation(host='localhost', port=8086)

    def test_retry_operation_success_first_try(self):
        """Test retry cuando la operacion tiene exito al primer intento."""
        mock_func = Mock(return_value='success')
        result = self.op._retry_operation(mock_func)

        self.assertEqual(result, 'success')
        self.assertEqual(mock_func.call_count, 1)

    def test_retry_operation_success_after_failures(self):
        """Test retry cuando la operacion tiene exito despues de fallos."""
        mock_func = Mock(side_effect=[Exception('fail'), Exception('fail'), 'success'])
        result = self.op._retry_operation(mock_func)

        self.assertEqual(result, 'success')
        self.assertEqual(mock_func.call_count, 3)

    def test_retry_operation_max_attempts(self):
        """Test retry cuando se alcanzan los intentos maximos."""
        mock_func = Mock(side_effect=Exception('fail'))

        with self.assertRaises(Exception):
            self.op._retry_operation(mock_func)

        self.assertEqual(mock_func.call_count, self.op._retry_attempts)


class TestInfluxdbOperationDataframe(unittest.TestCase):
    """Tests para operaciones con DataFrames."""

    @patch('influxdb.InfluxDBClient')
    def setUp(self, mock_client):
        """Setup para cada test."""
        self.op = InfluxdbOperation(host='localhost', port=8086, database='testdb')
        self.mock_client = mock_client.return_value

    def test_create_sample_dataframe(self):
        """Test creacion de DataFrame de muestra."""
        timestamps = pd.date_range(start='2024-01-01', periods=10, freq='1min')
        df = pd.DataFrame({
            'temperature': np.random.uniform(20, 30, 10),
            'humidity': np.random.uniform(40, 60, 10),
        }, index=timestamps)

        self.assertEqual(len(df), 10)
        self.assertIn('temperature', df.columns)
        self.assertIn('humidity', df.columns)

    def test_dataframe_with_nans(self):
        """Test validacion de DataFrame con NaNs."""
        timestamps = pd.date_range(start='2024-01-01', periods=5, freq='1min')
        df = pd.DataFrame({
            'value': [1.0, np.nan, 3.0, np.nan, 5.0],
        }, index=timestamps)

        # Verificar que hay NaNs
        self.assertTrue(df['value'].isna().any())
        self.assertEqual(df['value'].isna().sum(), 2)


class TestInfluxdbOperationOutliers(unittest.TestCase):
    """Tests para deteccion de outliers."""

    @patch('influxdb.InfluxDBClient')
    def setUp(self, mock_client):
        """Setup para cada test."""
        self.op = InfluxdbOperation(host='localhost', port=8086)

    def test_count_outliers_no_outliers(self):
        """Test contar outliers cuando no hay."""
        series = pd.Series([1, 2, 3, 4, 5])
        count = InfluxdbOperation._count_outliers(series)
        self.assertEqual(count, 0)

    def test_count_outliers_with_outliers(self):
        """Test contar outliers cuando hay."""
        # Serie con datos normales y un outlier claro
        # Usamos threshold más bajo para detectar el outlier
        series = pd.Series([10, 12, 11, 13, 10, 12, 11, 1000])
        count = InfluxdbOperation._count_outliers(series, threshold=2.0)
        self.assertGreater(count, 0)

    def test_count_outliers_empty_series(self):
        """Test contar outliers con serie vacia."""
        series = pd.Series([])
        count = InfluxdbOperation._count_outliers(series)
        self.assertEqual(count, 0)

    def test_count_outliers_single_value(self):
        """Test contar outliers con un solo valor."""
        series = pd.Series([1])
        count = InfluxdbOperation._count_outliers(series)
        self.assertEqual(count, 0)


if __name__ == '__main__':
    unittest.main()
