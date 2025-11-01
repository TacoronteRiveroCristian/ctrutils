"""
Tests básicos para la clase InfluxdbOperation mejorada.

Estos tests verifican las funcionalidades principales de validación,
limpieza de datos y operaciones administrativas.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ctrutils.database.influxdb import InfluxdbOperation


class TestInfluxdbOperation(unittest.TestCase):
    """Tests para la clase InfluxdbOperation."""

    def setUp(self):
        """Configuración para cada test."""
        # Mock del cliente InfluxDB
        self.mock_client = Mock()
        self.mock_client._host = 'localhost'
        self.mock_client._port = 8086
        self.mock_client._timeout = 5

        # Crear instancia con cliente mock
        self.influx = InfluxdbOperation(client=self.mock_client)

    def test_init_with_client(self):
        """Test: Crear instancia con cliente existente."""
        influx = InfluxdbOperation(client=self.mock_client)
        self.assertIsNotNone(influx)
        self.assertTrue(influx._is_external_client)
        self.assertEqual(influx._client, self.mock_client)

    def test_init_with_credentials(self):
        """Test: Crear instancia con credenciales."""
        with patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient'):
            influx = InfluxdbOperation(
                host='localhost',
                port=8086,
                username='admin',
                password='password'
            )
            self.assertIsNotNone(influx)
            self.assertFalse(influx._is_external_client)

    def test_init_without_params(self):
        """Test: Error al crear instancia sin parámetros."""
        with self.assertRaises(ValueError):
            InfluxdbOperation()

    def test_normalize_value_nan(self):
        """Test: Normalización de valores NaN."""
        # numpy NaN
        self.assertIsNone(self.influx.normalize_value_to_write(np.nan))

        # pandas NA
        self.assertIsNone(self.influx.normalize_value_to_write(pd.NA))

        # None
        self.assertIsNone(self.influx.normalize_value_to_write(None))

    def test_normalize_value_infinite(self):
        """Test: Normalización de valores infinitos."""
        self.assertIsNone(self.influx.normalize_value_to_write(np.inf))
        self.assertIsNone(self.influx.normalize_value_to_write(-np.inf))
        self.assertIsNone(self.influx.normalize_value_to_write(float('inf')))

    def test_normalize_value_numbers(self):
        """Test: Normalización de números válidos."""
        # Integer a float
        self.assertEqual(self.influx.normalize_value_to_write(42), 42.0)
        self.assertIsInstance(self.influx.normalize_value_to_write(42), float)

        # Float
        self.assertEqual(self.influx.normalize_value_to_write(42.5), 42.5)

        # Numpy int
        self.assertEqual(self.influx.normalize_value_to_write(np.int64(42)), 42.0)

        # Numpy float
        self.assertEqual(self.influx.normalize_value_to_write(np.float64(42.5)), 42.5)

    def test_normalize_value_strings(self):
        """Test: Normalización de strings."""
        # String válido
        self.assertEqual(self.influx.normalize_value_to_write("test"), "test")

        # String vacío
        self.assertIsNone(self.influx.normalize_value_to_write(""))
        self.assertIsNone(self.influx.normalize_value_to_write("   "))

        # Strings especiales
        self.assertIsNone(self.influx.normalize_value_to_write("nan"))
        self.assertIsNone(self.influx.normalize_value_to_write("NaN"))
        self.assertIsNone(self.influx.normalize_value_to_write("None"))
        self.assertIsNone(self.influx.normalize_value_to_write("null"))

    def test_normalize_value_boolean(self):
        """Test: Normalización de booleanos."""
        self.assertEqual(self.influx.normalize_value_to_write(True), True)
        self.assertEqual(self.influx.normalize_value_to_write(False), False)
        self.assertEqual(self.influx.normalize_value_to_write(np.bool_(True)), True)

    def test_validate_point_valid(self):
        """Test: Validación de punto válido."""
        point = {
            'measurement': 'test',
            'time': datetime.utcnow(),
            'fields': {
                'temperatura': 20.5,
                'humedad': 50.0
            }
        }

        validated = self.influx._validate_point(point)
        self.assertIsNotNone(validated)
        self.assertEqual(len(validated['fields']), 2)

    def test_validate_point_with_nan(self):
        """Test: Validación de punto con NaN."""
        point = {
            'measurement': 'test',
            'fields': {
                'temperatura': 20.5,
                'humedad': np.nan,
                'presion': 1013.0
            }
        }

        validated = self.influx._validate_point(point)
        self.assertIsNotNone(validated)
        # humedad debe ser eliminado
        self.assertEqual(len(validated['fields']), 2)
        self.assertNotIn('humedad', validated['fields'])

    def test_validate_point_all_nan(self):
        """Test: Validación de punto con todos los campos NaN."""
        point = {
            'measurement': 'test',
            'fields': {
                'temperatura': np.nan,
                'humedad': np.nan,
                'presion': np.inf
            }
        }

        validated = self.influx._validate_point(point)
        # Debe retornar None porque no hay campos válidos
        self.assertIsNone(validated)

    def test_validate_point_empty_fields(self):
        """Test: Validación de punto sin campos."""
        point = {
            'measurement': 'test',
            'fields': {}
        }

        validated = self.influx._validate_point(point)
        self.assertIsNone(validated)

    def test_write_dataframe_invalid_index(self):
        """Test: Error al escribir DataFrame sin DatetimeIndex."""
        df = pd.DataFrame({
            'temperatura': [20, 21, 22]
        })

        with self.assertRaises(TypeError):
            self.influx.write_dataframe(
                measurement='test',
                data=df,
                database='test_db'
            )

    def test_write_dataframe_no_data(self):
        """Test: Error al escribir sin datos."""
        with self.assertRaises(ValueError):
            self.influx.write_dataframe(
                measurement='test',
                data=None,
                database='test_db'
            )

    def test_write_dataframe_valid(self):
        """Test: Escribir DataFrame válido."""
        # Configurar mock
        self.mock_client.get_list_database.return_value = [{'name': 'test_db'}]
        self.mock_client.write_points.return_value = None

        # Crear DataFrame
        df = pd.DataFrame({
            'temperatura': [20.5, 21.0, 22.5],
            'humedad': [45.0, 50.0, 55.0]
        }, index=pd.date_range('2024-01-01', periods=3, freq='H'))

        # Escribir
        stats = self.influx.write_dataframe(
            measurement='test',
            data=df,
            database='test_db',
            batch_size=10
        )

        # Verificar estadísticas
        self.assertEqual(stats['total_points'], 3)
        self.assertEqual(stats['written_points'], 3)
        self.assertEqual(stats['invalid_points'], 0)

    def test_write_dataframe_with_nan(self):
        """Test: Escribir DataFrame con NaN."""
        self.mock_client.get_list_database.return_value = [{'name': 'test_db'}]
        self.mock_client.write_points.return_value = None

        df = pd.DataFrame({
            'temperatura': [20.5, np.nan, 22.5],
            'humedad': [45.0, 50.0, np.nan]
        }, index=pd.date_range('2024-01-01', periods=3, freq='H'))

        stats = self.influx.write_dataframe(
            measurement='test',
            data=df,
            database='test_db',
            validate_data=True
        )

        # Todos los puntos deben ser escritos (con campos parciales)
        self.assertEqual(stats['total_points'], 3)
        self.assertEqual(stats['written_points'], 3)

    def test_write_points_valid(self):
        """Test: Escribir puntos directamente."""
        self.mock_client.get_list_database.return_value = [{'name': 'test_db'}]
        self.mock_client.write_points.return_value = None

        points = [
            {
                'measurement': 'test',
                'time': datetime.utcnow(),
                'fields': {'valor': 10.0}
            },
            {
                'measurement': 'test',
                'time': datetime.utcnow(),
                'fields': {'valor': 20.0}
            }
        ]

        stats = self.influx.write_points(
            points=points,
            database='test_db'
        )

        self.assertEqual(stats['total_points'], 2)
        self.assertEqual(stats['written_points'], 2)

    def test_close_client_external(self):
        """Test: No cerrar cliente externo."""
        self.influx.close_client()
        # El cliente externo no debe ser cerrado
        self.mock_client.close.assert_not_called()

    def test_close_client_internal(self):
        """Test: Cerrar cliente interno."""
        with patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient') as MockClient:
            mock_instance = MockClient.return_value
            influx = InfluxdbOperation(host='localhost', port=8086)
            influx.close_client()
            # El cliente interno debe ser cerrado
            mock_instance.close.assert_called_once()

    def test_list_databases(self):
        """Test: Listar bases de datos."""
        self.mock_client.get_list_database.return_value = [
            {'name': 'db1'},
            {'name': 'db2'},
            {'name': 'db3'}
        ]

        databases = self.influx.list_databases()

        self.assertEqual(len(databases), 3)
        self.assertIn('db1', databases)
        self.assertIn('db2', databases)
        self.assertIn('db3', databases)

    def test_database_exists(self):
        """Test: Verificar existencia de base de datos."""
        self.mock_client.get_list_database.return_value = [
            {'name': 'db1'},
            {'name': 'db2'}
        ]

        self.assertTrue(self.influx.database_exists('db1'))
        self.assertFalse(self.influx.database_exists('db3'))

    def test_list_measurements(self):
        """Test: Listar mediciones."""
        self.mock_client.get_list_database.return_value = [{'name': 'test_db'}]

        mock_result = Mock()
        mock_result.get_points.return_value = [
            {'name': 'measurement1'},
            {'name': 'measurement2'}
        ]
        self.mock_client.query.return_value = mock_result

        measurements = self.influx.list_measurements('test_db')

        self.assertEqual(len(measurements), 2)
        self.assertIn('measurement1', measurements)
        self.assertIn('measurement2', measurements)

    def test_count_points(self):
        """Test: Contar puntos."""
        self.mock_client.get_list_database.return_value = [{'name': 'test_db'}]

        mock_result = Mock()
        mock_result.get_points.return_value = [
            {'count_value': 1234}
        ]
        self.mock_client.query.return_value = mock_result

        count = self.influx.count_points('test_measurement', 'test_db')

        self.assertEqual(count, 1234)


class TestInfluxdbOperationIntegration(unittest.TestCase):
    """Tests de integración (requieren InfluxDB corriendo)."""

    @unittest.skip("Requiere InfluxDB real para ejecutar")
    def test_real_connection(self):
        """Test de conexión real a InfluxDB."""
        # Este test se puede ejecutar manualmente si tienes InfluxDB corriendo
        influx = InfluxdbOperation(
            host='localhost',
            port=8086,
            username='admin',
            password='admin'
        )

        databases = influx.list_databases()
        self.assertIsInstance(databases, list)

        influx.close_client()


if __name__ == '__main__':
    unittest.main()
