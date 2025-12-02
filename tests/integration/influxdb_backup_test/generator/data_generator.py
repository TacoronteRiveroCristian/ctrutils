import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

from .schemas import DatabaseSchema, MeasurementSchema

logger = logging.getLogger(__name__)


class HeterogeneousDataGenerator:
    """Generates heterogeneous time-series data for testing"""

    def __init__(self, seed: int = 42):
        self.seed = seed
        np.random.seed(seed)
        self.schemas = self._create_schemas()
        logger.info(f"Initialized generator with {len(self.schemas)} database schemas")

    def _create_schemas(self) -> List[DatabaseSchema]:
        """Create 4 database schemas with heterogeneous data types"""
        return [
            self._create_iot_sensors_db(),
            self._create_application_metrics_db(),
            self._create_industrial_monitoring_db(),
            self._create_smart_building_db(),
        ]

    def _create_iot_sensors_db(self) -> DatabaseSchema:
        """IoT sensor data: temperature, humidity, pressure"""
        measurements = [
            MeasurementSchema(
                name='environment_sensors',
                fields={'temperature': 'float', 'humidity': 'float', 'pressure': 'float'},
                tags={
                    'location': ['room_1', 'room_2', 'room_3', 'outdoor'],
                    'sensor_type': ['DHT22', 'BME280', 'DS18B20'],
                    'floor': ['1', '2', '3']
                },
                frequency='10s'
            ),
            MeasurementSchema(
                name='motion_detectors',
                fields={'motion_detected': 'int', 'sensitivity': 'float'},
                tags={
                    'location': ['entrance', 'hallway', 'office_1', 'office_2'],
                    'sensor_model': ['PIR-100', 'PIR-200']
                },
                frequency='30s'
            ),
            MeasurementSchema(
                name='light_sensors',
                fields={'luminosity': 'float', 'uv_index': 'float'},
                tags={
                    'location': ['window_1', 'window_2', 'indoor'],
                    'type': ['ambient', 'direct']
                },
                frequency='15s'
            ),
            MeasurementSchema(
                name='air_quality',
                fields={'co2': 'int', 'voc': 'int', 'pm25': 'float', 'pm10': 'float'},
                tags={
                    'location': ['room_1', 'room_2', 'room_3'],
                    'sensor': ['MQ135', 'CCS811']
                },
                frequency='60s'
            ),
            MeasurementSchema(
                name='door_sensors',
                fields={'is_open': 'int', 'access_count': 'int'},
                tags={
                    'door_id': ['main_entrance', 'back_door', 'office_1', 'office_2'],
                    'security_level': ['high', 'medium', 'low']
                },
                frequency='5s'
            ),
            MeasurementSchema(
                name='water_sensors',
                fields={'leak_detected': 'int', 'moisture_level': 'float'},
                tags={
                    'location': ['bathroom', 'kitchen', 'basement'],
                    'sensor_type': ['capacitive', 'resistive']
                },
                frequency='20s'
            )
        ]
        return DatabaseSchema(
            name='iot_sensors',
            description='IoT sensor data from various devices',
            measurements=measurements
        )

    def _create_application_metrics_db(self) -> DatabaseSchema:
        """Application performance metrics"""
        measurements = [
            MeasurementSchema(
                name='system_resources',
                fields={
                    'cpu_usage': 'float',
                    'memory_usage': 'float',
                    'disk_io_read': 'int',
                    'disk_io_write': 'int',
                    'network_rx_bytes': 'int',
                    'network_tx_bytes': 'int'
                },
                tags={
                    'host': ['web-01', 'web-02', 'db-01', 'cache-01'],
                    'environment': ['production', 'staging'],
                    'datacenter': ['us-east', 'eu-west']
                },
                frequency='5s'
            ),
            MeasurementSchema(
                name='http_requests',
                fields={
                    'request_count': 'int',
                    'response_time_ms': 'float',
                    'error_count': 'int',
                    'status_2xx': 'int',
                    'status_4xx': 'int',
                    'status_5xx': 'int'
                },
                tags={
                    'endpoint': ['/api/users', '/api/products', '/api/orders', '/health'],
                    'method': ['GET', 'POST', 'PUT', 'DELETE'],
                    'service': ['api-gateway', 'auth-service', 'product-service']
                },
                frequency='10s'
            ),
            MeasurementSchema(
                name='database_metrics',
                fields={
                    'query_time_ms': 'float',
                    'connection_count': 'int',
                    'slow_queries': 'int',
                    'deadlocks': 'int'
                },
                tags={
                    'db_name': ['users_db', 'products_db', 'analytics_db'],
                    'db_type': ['postgres', 'mysql', 'mongodb']
                },
                frequency='15s'
            ),
            MeasurementSchema(
                name='cache_metrics',
                fields={
                    'hit_rate': 'float',
                    'miss_count': 'int',
                    'eviction_count': 'int',
                    'memory_usage_mb': 'float'
                },
                tags={
                    'cache_name': ['session', 'api', 'product', 'user'],
                    'cache_type': ['redis', 'memcached']
                },
                frequency='10s'
            ),
            MeasurementSchema(
                name='application_errors',
                fields={
                    'error_count': 'int',
                    'critical_errors': 'int',
                    'warnings': 'int'
                },
                tags={
                    'service': ['web', 'api', 'worker', 'scheduler'],
                    'error_type': ['exception', 'timeout', 'validation'],
                    'severity': ['critical', 'high', 'medium', 'low']
                },
                frequency='30s'
            ),
            MeasurementSchema(
                name='background_jobs',
                fields={
                    'jobs_queued': 'int',
                    'jobs_processing': 'int',
                    'jobs_completed': 'int',
                    'jobs_failed': 'int',
                    'avg_processing_time_s': 'float'
                },
                tags={
                    'queue_name': ['email', 'reports', 'notifications', 'cleanup'],
                    'priority': ['high', 'normal', 'low']
                },
                frequency='20s'
            ),
            MeasurementSchema(
                name='business_metrics',
                fields={
                    'active_users': 'int',
                    'transactions': 'int',
                    'revenue_cents': 'int',
                    'conversion_rate': 'float'
                },
                tags={
                    'platform': ['web', 'mobile', 'api'],
                    'region': ['us', 'eu', 'asia']
                },
                frequency='60s'
            )
        ]
        return DatabaseSchema(
            name='app_metrics',
            description='Application performance and business metrics',
            measurements=measurements
        )

    def _create_industrial_monitoring_db(self) -> DatabaseSchema:
        """Industrial equipment monitoring"""
        measurements = [
            MeasurementSchema(
                name='machine_sensors',
                fields={
                    'vibration': 'float',
                    'temperature': 'float',
                    'rpm': 'int',
                    'power_consumption_kw': 'float'
                },
                tags={
                    'machine_id': ['CNC-01', 'CNC-02', 'PRESS-01', 'LATHE-01'],
                    'zone': ['assembly', 'machining', 'quality_control']
                },
                frequency='5s'
            ),
            MeasurementSchema(
                name='production_line',
                fields={
                    'units_produced': 'int',
                    'defect_count': 'int',
                    'cycle_time_s': 'float',
                    'efficiency_pct': 'float'
                },
                tags={
                    'line_id': ['LINE-A', 'LINE-B', 'LINE-C'],
                    'shift': ['morning', 'afternoon', 'night']
                },
                frequency='60s'
            ),
            MeasurementSchema(
                name='energy_consumption',
                fields={
                    'voltage': 'float',
                    'current': 'float',
                    'power_kw': 'float',
                    'power_factor': 'float'
                },
                tags={
                    'meter_id': ['MAIN-01', 'SUB-01', 'SUB-02'],
                    'zone': ['production', 'office', 'warehouse']
                },
                frequency='10s'
            ),
            MeasurementSchema(
                name='conveyor_belts',
                fields={
                    'speed_mps': 'float',
                    'load_kg': 'float',
                    'motor_temp': 'float'
                },
                tags={
                    'belt_id': ['CONV-A', 'CONV-B', 'CONV-C'],
                    'status': ['running', 'idle']
                },
                frequency='15s'
            ),
            MeasurementSchema(
                name='safety_systems',
                fields={
                    'emergency_stops': 'int',
                    'alarm_count': 'int',
                    'guard_status': 'int'
                },
                tags={
                    'zone': ['assembly', 'machining', 'shipping'],
                    'alarm_type': ['critical', 'warning', 'info']
                },
                frequency='5s'
            )
        ]
        return DatabaseSchema(
            name='industrial_monitoring',
            description='Industrial equipment and production monitoring',
            measurements=measurements
        )

    def _create_smart_building_db(self) -> DatabaseSchema:
        """Smart building automation"""
        measurements = [
            MeasurementSchema(
                name='hvac_systems',
                fields={
                    'setpoint_temp': 'float',
                    'actual_temp': 'float',
                    'fan_speed_pct': 'float',
                    'power_consumption_kw': 'float'
                },
                tags={
                    'zone': ['north', 'south', 'east', 'west', 'central'],
                    'system_id': ['AHU-01', 'AHU-02', 'FCU-01', 'FCU-02']
                },
                frequency='30s'
            ),
            MeasurementSchema(
                name='lighting_control',
                fields={
                    'brightness_pct': 'float',
                    'power_consumption_w': 'float',
                    'occupancy': 'int'
                },
                tags={
                    'room': ['conference_1', 'conference_2', 'office_floor_1', 'lobby'],
                    'light_type': ['LED', 'fluorescent']
                },
                frequency='60s'
            ),
            MeasurementSchema(
                name='elevator_systems',
                fields={
                    'trips_count': 'int',
                    'wait_time_s': 'float',
                    'current_floor': 'int',
                    'door_cycles': 'int'
                },
                tags={
                    'elevator_id': ['ELEV-A', 'ELEV-B', 'ELEV-C'],
                    'status': ['active', 'maintenance']
                },
                frequency='10s'
            ),
            MeasurementSchema(
                name='security_cameras',
                fields={
                    'motion_detected': 'int',
                    'recording_status': 'int',
                    'storage_used_gb': 'float'
                },
                tags={
                    'camera_id': ['CAM-01', 'CAM-02', 'CAM-03', 'CAM-04'],
                    'location': ['entrance', 'parking', 'lobby', 'roof']
                },
                frequency='15s'
            ),
            MeasurementSchema(
                name='access_control',
                fields={
                    'access_granted': 'int',
                    'access_denied': 'int',
                    'card_reads': 'int'
                },
                tags={
                    'reader_id': ['READER-01', 'READER-02', 'READER-03'],
                    'access_level': ['employee', 'visitor', 'admin']
                },
                frequency='5s'
            ),
            MeasurementSchema(
                name='fire_safety',
                fields={
                    'smoke_level': 'float',
                    'alarm_status': 'int',
                    'sprinkler_status': 'int'
                },
                tags={
                    'zone': ['floor_1', 'floor_2', 'floor_3', 'basement'],
                    'detector_type': ['smoke', 'heat', 'co']
                },
                frequency='10s'
            ),
            MeasurementSchema(
                name='parking_sensors',
                fields={
                    'occupied_spaces': 'int',
                    'available_spaces': 'int',
                    'avg_occupancy_time_min': 'float'
                },
                tags={
                    'level': ['P1', 'P2', 'P3', 'ground'],
                    'section': ['A', 'B', 'C']
                },
                frequency='30s'
            )
        ]
        return DatabaseSchema(
            name='smart_building',
            description='Smart building automation and monitoring',
            measurements=measurements
        )

    def generate_point(
        self,
        measurement: MeasurementSchema,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """Generate single data point for a measurement"""
        fields = {}
        for field_name, field_type in measurement.fields.items():
            if field_type == 'float':
                fields[field_name] = self._generate_float(field_name)
            elif field_type == 'int':
                fields[field_name] = self._generate_int(field_name)

        tags = {
            tag_name: np.random.choice(values)
            for tag_name, values in measurement.tags.items()
        }

        return {
            'measurement': measurement.name,
            'time': timestamp.isoformat() + 'Z',
            'fields': fields,
            'tags': tags
        }

    def _generate_float(self, field_name: str) -> float:
        """Generate realistic float values based on field name patterns"""
        field_lower = field_name.lower()

        # Temperature fields
        if 'temperature' in field_lower or 'temp' in field_lower:
            if 'motor' in field_lower or 'machine' in field_lower:
                return float(np.random.normal(65.0, 10.0))
            elif 'setpoint' in field_lower:
                return float(np.random.normal(22.0, 1.0))
            return float(np.random.normal(22.0, 3.0))

        # Humidity
        elif 'humidity' in field_lower or 'moisture' in field_lower:
            return float(np.clip(np.random.normal(50.0, 15.0), 0, 100))

        # Pressure
        elif 'pressure' in field_lower:
            return float(np.random.normal(1013.25, 10.0))

        # CPU/Memory usage
        elif 'cpu' in field_lower or 'memory' in field_lower:
            return float(np.clip(np.random.gamma(2, 15), 0, 100))

        # Response time
        elif 'response_time' in field_lower or 'query_time' in field_lower or 'wait_time' in field_lower:
            return float(np.clip(np.random.exponential(50), 1, 5000))

        # Percentages
        elif 'pct' in field_lower or 'rate' in field_lower or 'efficiency' in field_lower:
            return float(np.clip(np.random.beta(8, 2) * 100, 0, 100))

        # Power consumption
        elif 'power' in field_lower or 'consumption' in field_lower:
            if 'kw' in field_lower:
                return float(np.clip(np.random.gamma(3, 2), 0.5, 50))
            else:  # watts
                return float(np.clip(np.random.gamma(4, 50), 10, 1000))

        # Vibration
        elif 'vibration' in field_lower:
            return float(np.clip(np.random.normal(0.5, 0.2), 0, 5))

        # Speed
        elif 'speed' in field_lower:
            return float(np.clip(np.random.normal(1.5, 0.3), 0, 5))

        # Luminosity
        elif 'luminosity' in field_lower or 'brightness' in field_lower:
            return float(np.clip(np.random.gamma(5, 10), 0, 100))

        # UV index
        elif 'uv' in field_lower:
            return float(np.clip(np.random.gamma(2, 1), 0, 11))

        # PM2.5, PM10
        elif 'pm' in field_lower:
            return float(np.clip(np.random.exponential(15), 0, 150))

        # Voltage, Current, Power Factor
        elif 'voltage' in field_lower:
            return float(np.random.normal(230.0, 5.0))
        elif 'current' in field_lower:
            return float(np.clip(np.random.gamma(3, 5), 0, 100))
        elif 'factor' in field_lower:
            return float(np.clip(np.random.normal(0.95, 0.05), 0.7, 1.0))

        # Load
        elif 'load' in field_lower:
            return float(np.clip(np.random.gamma(4, 20), 0, 500))

        # Smoke level
        elif 'smoke' in field_lower:
            return float(np.clip(np.random.exponential(2), 0, 10))

        # Storage
        elif 'storage' in field_lower:
            return float(np.clip(np.random.gamma(5, 2), 0, 100))

        # Sensitivity
        elif 'sensitivity' in field_lower:
            return float(np.random.uniform(0.5, 1.0))

        # Processing time
        elif 'processing' in field_lower:
            return float(np.clip(np.random.exponential(30), 1, 300))

        # Conversion rate
        elif 'conversion' in field_lower:
            return float(np.clip(np.random.beta(2, 5) * 100, 0, 100))

        # Cycle time
        elif 'cycle' in field_lower:
            return float(np.clip(np.random.normal(45.0, 10.0), 10, 120))

        # Occupancy time
        elif 'occupancy_time' in field_lower:
            return float(np.clip(np.random.exponential(60), 5, 300))

        # Default: uniform distribution
        else:
            return float(np.random.uniform(0, 100))

    def _generate_int(self, field_name: str) -> int:
        """Generate realistic integer values based on field name patterns"""
        field_lower = field_name.lower()

        # Counters
        if 'count' in field_lower:
            if 'error' in field_lower or 'defect' in field_lower or 'failed' in field_lower:
                return int(np.random.poisson(0.5))
            elif 'alarm' in field_lower or 'emergency' in field_lower:
                return int(np.random.poisson(0.1))
            elif 'request' in field_lower or 'transaction' in field_lower:
                return int(np.random.poisson(100))
            elif 'connection' in field_lower:
                return int(np.random.poisson(20))
            elif 'access' in field_lower or 'door' in field_lower or 'card' in field_lower:
                return int(np.random.poisson(5))
            elif 'trip' in field_lower:
                return int(np.random.poisson(3))
            return int(np.random.poisson(10))

        # Detected/Status/Boolean flags
        elif 'detected' in field_lower or 'status' in field_lower or 'is_open' in field_lower or 'occupancy' in field_lower:
            return int(np.random.choice([0, 1], p=[0.7, 0.3]))

        # Granted/Denied
        elif 'granted' in field_lower:
            return int(np.random.poisson(10))
        elif 'denied' in field_lower:
            return int(np.random.poisson(1))

        # RPM
        elif 'rpm' in field_lower:
            return int(np.random.normal(1500, 200))

        # Floor numbers
        elif 'floor' in field_lower and 'current' in field_lower:
            return int(np.random.randint(1, 20))

        # Large counters (bytes)
        elif 'bytes' in field_lower:
            return int(np.random.exponential(1000000))

        # CO2, VOC
        elif 'co2' in field_lower:
            return int(np.random.normal(450, 100))
        elif 'voc' in field_lower:
            return int(np.random.normal(100, 30))

        # Users
        elif 'user' in field_lower and 'active' in field_lower:
            return int(np.random.poisson(500))

        # Revenue (cents)
        elif 'revenue' in field_lower:
            return int(np.random.exponential(100000))

        # Units produced
        elif 'units' in field_lower or 'produced' in field_lower:
            return int(np.random.poisson(50))

        # Slow queries, deadlocks
        elif 'slow' in field_lower or 'deadlock' in field_lower:
            return int(np.random.poisson(0.5))

        # Jobs
        elif 'job' in field_lower:
            if 'queued' in field_lower:
                return int(np.random.poisson(15))
            elif 'processing' in field_lower:
                return int(np.random.poisson(5))
            elif 'completed' in field_lower:
                return int(np.random.poisson(100))
            elif 'failed' in field_lower:
                return int(np.random.poisson(2))

        # Critical errors, warnings
        elif 'critical' in field_lower:
            return int(np.random.poisson(0.2))
        elif 'warning' in field_lower:
            return int(np.random.poisson(5))

        # Status codes
        elif 'status_2' in field_lower or '2xx' in field_lower:
            return int(np.random.poisson(90))
        elif 'status_4' in field_lower or '4xx' in field_lower:
            return int(np.random.poisson(8))
        elif 'status_5' in field_lower or '5xx' in field_lower:
            return int(np.random.poisson(2))

        # Spaces (parking)
        elif 'spaces' in field_lower:
            if 'occupied' in field_lower:
                return int(np.random.randint(20, 80))
            elif 'available' in field_lower:
                return int(np.random.randint(10, 50))

        # Eviction, miss
        elif 'eviction' in field_lower or 'miss' in field_lower:
            return int(np.random.poisson(3))

        # Default: small poisson
        else:
            return int(np.random.poisson(5))

    def generate_bulk_data(
        self,
        database: DatabaseSchema,
        hours: int = 1
    ) -> Dict[str, pd.DataFrame]:
        """Generate bulk historical data for all measurements in a database"""
        result = {}

        for measurement in database.measurements:
            logger.info(
                f"Generating {hours}h of data for {database.name}.{measurement.name} "
                f"(frequency: {measurement.frequency})"
            )

            # Generate timestamps
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            timestamps = pd.date_range(
                start=start_time,
                end=end_time,
                freq=measurement.frequency
            )

            # Generate points
            points = [
                self.generate_point(measurement, ts.to_pydatetime())
                for ts in timestamps
            ]

            # Convert to DataFrame
            df = self._points_to_dataframe(points)
            result[measurement.name] = df

            logger.info(f"Generated {len(df)} points for {measurement.name}")

        return result

    def _points_to_dataframe(self, points: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert list of points to DataFrame compatible with InfluxdbOperation"""
        if not points:
            return pd.DataFrame()

        # Extract timestamps
        timestamps = [
            pd.to_datetime(p['time']) for p in points
        ]

        # Extract fields
        fields_data = {
            field_name: [p['fields'].get(field_name) for p in points]
            for field_name in points[0]['fields'].keys()
        }

        # Create DataFrame with timestamps as index
        df = pd.DataFrame(fields_data, index=timestamps)
        df.index.name = 'time'

        # Store tags as metadata (to be passed separately to write_dataframe)
        df._tags = points[0]['tags']

        return df
