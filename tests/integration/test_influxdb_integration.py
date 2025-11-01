"""Tests de integracion para InfluxdbOperation.

NOTA: Estos tests requieren una instancia de InfluxDB corriendo.
Configurar las siguientes variables de entorno:
- INFLUXDB_TEST_HOST (default: localhost)
- INFLUXDB_TEST_PORT (default: 8086)
- INFLUXDB_TEST_USER (default: admin)
- INFLUXDB_TEST_PASSWORD (default: admin)
- INFLUXDB_TEST_DATABASE (default: test_db)

Para ejecutar solo tests de integracion:
    pytest tests/integration/ -v

Para saltar tests de integracion:
    pytest tests/unit/ -v
"""
import unittest
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ctrutils.database.influxdb import InfluxdbOperation
from tests.fixtures import (
    get_test_config,
    create_sample_dataframe,
    create_time_series_with_gaps,
)


# Skip tests si no hay configuracion de InfluxDB
SKIP_INTEGRATION = not os.getenv('INFLUXDB_TEST_HOST') and not os.path.exists('/usr/bin/influxd')
SKIP_MSG = "Requiere InfluxDB. Configurar INFLUXDB_TEST_HOST o instalar InfluxDB localmente."


@unittest.skipIf(SKIP_INTEGRATION, SKIP_MSG)
class TestInfluxdbOperationIntegration(unittest.TestCase):
    """Tests de integracion con InfluxDB real."""
    
    @classmethod
    def setUpClass(cls):
        """Setup una vez para toda la clase."""
        cls.config = get_test_config()
        cls.test_database = cls.config['database']
        cls.test_measurement = 'test_measurement'
    
    def setUp(self):
        """Setup para cada test."""
        try:
            self.op = InfluxdbOperation(
                host=self.config['host'],
                port=self.config['port'],
                username=self.config['username'],
                password=self.config['password'],
            )
            
            # Crear base de datos de test
            self.op.create_database(self.test_database)
            self.op.switch_database(self.test_database)
            
        except Exception as e:
            self.skipTest(f"No se pudo conectar a InfluxDB: {e}")
    
    def tearDown(self):
        """Limpieza despues de cada test."""
        try:
            # Limpiar datos de test
            if hasattr(self, 'op') and self.op:
                measurements = self.op.get_measurements()
                for measurement in measurements:
                    self.op.delete(measurement)
        except:
            pass
    
    @classmethod
    def tearDownClass(cls):
        """Limpieza final."""
        try:
            config = get_test_config()
            op = InfluxdbOperation(
                host=config['host'],
                port=config['port'],
                username=config['username'],
                password=config['password'],
            )
            op.drop_database(cls.test_database)
        except:
            pass
    
    def test_write_and_read_points(self):
        """Test escribir y leer puntos."""
        points = [
            {
                "measurement": self.test_measurement,
                "time": "2024-01-01T00:00:00Z",
                "fields": {"value": 25.5},
                "tags": {"location": "room_1"},
            },
            {
                "measurement": self.test_measurement,
                "time": "2024-01-01T00:01:00Z",
                "fields": {"value": 26.0},
                "tags": {"location": "room_1"},
            },
        ]
        
        # Escribir
        stats = self.op.write_points(points)
        self.assertEqual(stats['successful'], 2)
        self.assertEqual(stats['failed'], 0)
        
        # Leer
        df = self.op.query_to_dataframe(
            measurement=self.test_measurement,
            start_time='2024-01-01T00:00:00Z',
            end_time='2024-01-01T00:02:00Z'
        )
        
        self.assertFalse(df.empty)
        self.assertGreaterEqual(len(df), 2)
    
    def test_write_dataframe(self):
        """Test escribir DataFrame."""
        df = create_sample_dataframe(rows=50, with_nans=True)
        
        stats = self.op.write_dataframe(
            df=df,
            measurement=self.test_measurement,
            tags={'sensor': 'DHT22'},
            validate_data=True
        )
        
        self.assertGreater(stats['successful'], 0)
        
        # Verificar que se escribio
        measurements = self.op.get_measurements()
        self.assertIn(self.test_measurement, measurements)
    
    def test_create_and_list_databases(self):
        """Test crear y listar bases de datos."""
        test_db_name = 'temp_test_db'
        
        # Crear
        self.op.create_database(test_db_name)
        
        # Listar
        databases = self.op.get_databases()
        self.assertIn(test_db_name, databases)
        
        # Limpiar
        self.op.drop_database(test_db_name)
    
    def test_retention_policy(self):
        """Test crear y listar retention policies."""
        rp_name = 'test_rp'
        
        # Crear
        self.op.create_retention_policy(
            name=rp_name,
            duration='1d',
            replication=1,
            database=self.test_database
        )
        
        # Listar
        policies = self.op.get_retention_policies(self.test_database)
        policy_names = [p['name'] for p in policies]
        self.assertIn(rp_name, policy_names)
        
        # Limpiar
        self.op.drop_retention_policy(rp_name, self.test_database)
    
    def test_continuous_query(self):
        """Test crear y listar continuous queries."""
        # Primero escribir algunos datos
        df = create_sample_dataframe(rows=100)
        self.op.write_dataframe(df, measurement=self.test_measurement)
        
        cq_name = 'test_cq'
        target_measurement = 'downsampled_data'
        
        # Crear CQ
        self.op.create_continuous_query(
            cq_name=cq_name,
            measurement=self.test_measurement,
            target_measurement=target_measurement,
            aggregation_window='10m',
            aggregation_func='MEAN',
            database=self.test_database
        )
        
        # Listar
        cqs = self.op.list_continuous_queries(self.test_database)
        cq_names = [cq.get('name') for cq in cqs if cq.get('name')]
        self.assertIn(cq_name, cq_names)
        
        # Limpiar
        self.op.drop_continuous_query(cq_name, self.test_database)
    
    def test_backup_and_restore(self):
        """Test backup y restore de measurement."""
        import tempfile
        
        # Escribir datos originales
        df_original = create_sample_dataframe(rows=50)
        self.op.write_dataframe(df_original, measurement=self.test_measurement)
        
        # Backup
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            backup_file = f.name
        
        try:
            points_exported = self.op.backup_measurement(
                measurement=self.test_measurement,
                output_file=backup_file
            )
            self.assertGreater(points_exported, 0)
            
            # Eliminar datos originales
            self.op.delete(self.test_measurement)
            
            # Restore
            stats = self.op.restore_measurement(
                measurement=self.test_measurement,
                input_file=backup_file
            )
            self.assertGreater(stats['successful'], 0)
            
            # Verificar
            df_restored = self.op.query_to_dataframe(measurement=self.test_measurement)
            self.assertFalse(df_restored.empty)
            
        finally:
            if os.path.exists(backup_file):
                os.remove(backup_file)
    
    def test_data_quality_metrics(self):
        """Test calcular metricas de calidad de datos."""
        # Crear datos con caracteristicas conocidas
        df = create_sample_dataframe(rows=100, with_nans=True)
        self.op.write_dataframe(df, measurement=self.test_measurement)
        
        # Calcular metricas
        metrics = self.op.calculate_data_quality_metrics(
            measurement=self.test_measurement
        )
        
        self.assertIsInstance(metrics, dict)
        self.assertGreater(len(metrics), 0)
        
        # Verificar estructura de metricas
        for field, field_metrics in metrics.items():
            self.assertIn('count', field_metrics)
            self.assertIn('missing', field_metrics)
            self.assertIn('missing_percentage', field_metrics)
    
    def test_downsampling(self):
        """Test downsampling de datos."""
        # Crear datos con alta frecuencia
        timestamps = pd.date_range(start='2024-01-01', periods=1000, freq='1min')
        df = pd.DataFrame({
            'value': np.random.uniform(20, 30, 1000),
        }, index=timestamps)
        
        self.op.write_dataframe(df, measurement=self.test_measurement)
        
        # Downsample
        target_measurement = 'downsampled_test'
        points_created = self.op.downsample_data(
            measurement=self.test_measurement,
            target_measurement=target_measurement,
            aggregation_window='1h',
            aggregation_func='MEAN',
            start_time='2024-01-01T00:00:00Z',
            end_time='2024-01-02T00:00:00Z'
        )
        
        self.assertGreater(points_created, 0)
        
        # Verificar que el measurement downsampled existe
        measurements = self.op.get_measurements()
        self.assertIn(target_measurement, measurements)
    
    def test_field_keys_grouped_by_type(self):
        """Test obtener fields agrupados por tipo."""
        # Escribir datos con diferentes tipos
        df = pd.DataFrame({
            'temperature': [25.5, 26.0, 25.8],
            'humidity': [60, 65, 62],
        }, index=pd.date_range(start='2024-01-01', periods=3, freq='1min'))
        
        self.op.write_dataframe(df, measurement=self.test_measurement)
        
        # Obtener fields por tipo
        fields_by_type = self.op.get_field_keys_grouped_by_type(self.test_measurement)
        
        self.assertIsInstance(fields_by_type, dict)
        self.assertGreater(len(fields_by_type), 0)


@unittest.skipIf(SKIP_INTEGRATION, SKIP_MSG)
class TestInfluxdbOperationPerformance(unittest.TestCase):
    """Tests de performance con datos grandes."""
    
    @classmethod
    def setUpClass(cls):
        """Setup una vez para toda la clase."""
        cls.config = get_test_config()
        cls.test_database = cls.config['database'] + '_perf'
    
    def setUp(self):
        """Setup para cada test."""
        try:
            self.op = InfluxdbOperation(
                host=self.config['host'],
                port=self.config['port'],
                username=self.config['username'],
                password=self.config['password'],
            )
            self.op.create_database(self.test_database)
            self.op.switch_database(self.test_database)
            self.op.enable_logging()
            
        except Exception as e:
            self.skipTest(f"No se pudo conectar a InfluxDB: {e}")
    
    def tearDown(self):
        """Limpieza."""
        try:
            if hasattr(self, 'op') and self.op:
                self.op.drop_database(self.test_database)
        except:
            pass
    
    def test_write_large_dataframe(self):
        """Test escribir DataFrame grande."""
        # Crear DataFrame con 10k filas
        timestamps = pd.date_range(start='2024-01-01', periods=10000, freq='1s')
        df = pd.DataFrame({
            'cpu': np.random.uniform(0, 100, 10000),
            'memory': np.random.uniform(0, 100, 10000),
        }, index=timestamps)
        
        # Escribir
        stats = self.op.write_dataframe(
            df=df,
            measurement='performance_test',
            batch_size=1000
        )
        
        self.assertEqual(stats['successful'], 10000)
        self.assertGreater(stats['points_per_second'], 0)
        
        # Verificar metricas
        metrics = self.op.get_metrics()
        self.assertGreater(metrics['total_points'], 0)
    
    def test_write_dataframe_parallel(self):
        """Test escritura paralela."""
        # Crear DataFrame grande
        timestamps = pd.date_range(start='2024-01-01', periods=10000, freq='1s')
        df = pd.DataFrame({
            'value1': np.random.uniform(0, 100, 10000),
            'value2': np.random.uniform(0, 100, 10000),
        }, index=timestamps)
        
        # Escribir en paralelo
        stats = self.op.write_dataframe_parallel(
            df=df,
            measurement='parallel_test',
            batch_size=1000,
            max_workers=4
        )
        
        self.assertGreater(stats['successful'], 0)
        self.assertGreater(stats['points_per_second'], 0)
        print(f"Performance: {stats['points_per_second']:.2f} points/sec")


if __name__ == '__main__':
    unittest.main()
