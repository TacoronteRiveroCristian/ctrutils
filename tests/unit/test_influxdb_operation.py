"""Tests unitarios para InfluxdbOperation."""
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone
import pandas as pd
import numpy as np

from ctrutils.database.influxdb import InfluxdbOperation


class TestInfluxdbOperationInit(unittest.TestCase):
    """Tests para inicializacion de InfluxdbOperation."""

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_init_with_all_params(self, mock_client):
        """Test inicializacion con todos los parametros."""
        op = InfluxdbOperation(
            host='localhost',
            port=8086,
            username='user',
            password='pass',
            database='testdb',
            ssl=True,
            verify_ssl=True
        )

        self.assertEqual(op._host, 'localhost')
        self.assertEqual(op._port, 8086)
        self.assertEqual(op._database, 'testdb')
        mock_client.assert_called_once()

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_init_without_database(self, mock_client):
        """Test inicializacion sin base de datos."""
        op = InfluxdbOperation(host='localhost', port=8086)
        self.assertIsNone(op._database)


class TestInfluxdbOperationDataValidation(unittest.TestCase):
    """Tests para validacion de datos."""

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def setUp(self, mock_client):
        """Setup para cada test."""
        self.op = InfluxdbOperation(host='localhost', port=8086)
        self.mock_client = mock_client

    def test_validate_value_with_nan(self):
        """Test validacion con NaN."""
        result = self.op._validate_value(np.nan)
        self.assertIsNone(result)

    def test_validate_value_with_inf(self):
        """Test validacion con infinito."""
        result = self.op._validate_value(np.inf)
        self.assertIsNone(result)

        result = self.op._validate_value(-np.inf)
        self.assertIsNone(result)

    def test_validate_value_with_none(self):
        """Test validacion con None."""
        result = self.op._validate_value(None)
        self.assertIsNone(result)

    def test_validate_value_with_valid_number(self):
        """Test validacion con numero valido."""
        result = self.op._validate_value(42.5)
        self.assertEqual(result, 42.5)

    def test_validate_value_with_valid_string(self):
        """Test validacion con string valido."""
        result = self.op._validate_value("test")
        self.assertEqual(result, "test")

    def test_validate_value_with_numpy_types(self):
        """Test validacion con tipos numpy."""
        result = self.op._validate_value(np.int64(42))
        self.assertEqual(result, 42)

        result = self.op._validate_value(np.float64(3.14))
        self.assertAlmostEqual(result, 3.14)


class TestInfluxdbOperationDateConversion(unittest.TestCase):
    """Tests para conversion de fechas."""

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def setUp(self, mock_client):
        """Setup para cada test."""
        self.op = InfluxdbOperation(host='localhost', port=8086)

    def test_convert_to_utc_iso_with_datetime(self):
        """Test conversion de datetime a UTC ISO."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = self.op._convert_to_utc_iso(dt)
        self.assertEqual(result, '2024-01-01T12:00:00+00:00')

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

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
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

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
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

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def setUp(self, mock_client):
        """Setup para cada test."""
        self.op = InfluxdbOperation(host='localhost', port=8086)

    def test_query_builder_simple(self):
        """Test query builder simple."""
        query = self.op.query_builder(measurement='temperature')
        self.assertEqual(query, 'SELECT * FROM "temperature"')

    def test_query_builder_with_fields(self):
        """Test query builder con campos especificos."""
        query = self.op.query_builder(
            measurement='temperature',
            fields=['value', 'sensor_id']
        )
        self.assertEqual(query, 'SELECT value, sensor_id FROM "temperature"')

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

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
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

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
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

    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def setUp(self, mock_client):
        """Setup para cada test."""
        self.op = InfluxdbOperation(host='localhost', port=8086)

    def test_count_outliers_no_outliers(self):
        """Test contar outliers cuando no hay."""
        series = pd.Series([1, 2, 3, 4, 5])
        count = self.op._count_outliers(series)
        self.assertEqual(count, 0)

    def test_count_outliers_with_outliers(self):
        """Test contar outliers cuando hay."""
        series = pd.Series([1, 2, 3, 4, 5, 100])  # 100 es un outlier
        count = self.op._count_outliers(series)
        self.assertGreater(count, 0)

    def test_count_outliers_empty_series(self):
        """Test contar outliers con serie vacia."""
        series = pd.Series([])
        count = self.op._count_outliers(series)
        self.assertEqual(count, 0)

    def test_count_outliers_single_value(self):
        """Test contar outliers con un solo valor."""
        series = pd.Series([1])
        count = self.op._count_outliers(series)
        self.assertEqual(count, 0)


if __name__ == '__main__':
    unittest.main()
