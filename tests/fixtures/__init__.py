"""Fixtures compartidos para tests."""
import os
from typing import Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def get_test_config() -> Dict[str, Any]:
    """
    Obtiene configuracion para tests desde variables de entorno.

    Para tests de integracion, configurar:
    - INFLUXDB_TEST_HOST
    - INFLUXDB_TEST_PORT
    - INFLUXDB_TEST_USER
    - INFLUXDB_TEST_PASSWORD
    - INFLUXDB_TEST_DATABASE
    """
    return {
        'host': os.getenv('INFLUXDB_TEST_HOST', 'localhost'),
        'port': int(os.getenv('INFLUXDB_TEST_PORT', 8086)),
        'username': os.getenv('INFLUXDB_TEST_USER', 'admin'),
        'password': os.getenv('INFLUXDB_TEST_PASSWORD', 'admin'),
        'database': os.getenv('INFLUXDB_TEST_DATABASE', 'test_db'),
    }


def create_sample_dataframe(
    rows: int = 100,
    with_nans: bool = False,
    with_infs: bool = False,
    numeric_only: bool = True,
) -> pd.DataFrame:
    """
    Crea un DataFrame de ejemplo para tests.

    Args:
        rows: Numero de filas
        with_nans: Si incluir valores NaN
        with_infs: Si incluir valores infinitos
        numeric_only: Si solo incluir columnas numericas

    Returns:
        DataFrame de prueba con timestamp como index
    """
    # Crear timestamps
    start_date = datetime(2024, 1, 1)
    timestamps = [start_date + timedelta(minutes=i) for i in range(rows)]

    data = {
        'temperature': np.random.uniform(20, 30, rows),
        'humidity': np.random.uniform(40, 60, rows),
        'pressure': np.random.uniform(1000, 1020, rows),
    }

    if not numeric_only:
        data['location'] = ['site_A' if i % 2 == 0 else 'site_B' for i in range(rows)]
        data['status'] = np.random.choice(['ok', 'warning', 'error'], rows)

    df = pd.DataFrame(data, index=timestamps)
    df.index.name = 'time'

    # Añadir NaNs
    if with_nans:
        nan_indices = np.random.choice(rows, size=rows // 10, replace=False)
        for col in ['temperature', 'humidity']:
            df.loc[df.index[nan_indices[:len(nan_indices)//2]], col] = np.nan

    # Añadir infinitos
    if with_infs:
        inf_indices = np.random.choice(rows, size=rows // 20, replace=False)
        df.loc[df.index[inf_indices[:len(inf_indices)//2]], 'temperature'] = np.inf
        df.loc[df.index[inf_indices[len(inf_indices)//2:]], 'temperature'] = -np.inf

    return df


def create_time_series_with_gaps(
    total_hours: int = 24,
    gap_percentage: float = 0.2,
) -> pd.DataFrame:
    """
    Crea una serie temporal con gaps (datos faltantes).

    Args:
        total_hours: Total de horas de datos
        gap_percentage: Porcentaje de datos faltantes (0-1)

    Returns:
        DataFrame con gaps en los datos
    """
    timestamps = pd.date_range(
        start='2024-01-01',
        periods=total_hours * 60,  # Un dato por minuto
        freq='1min'
    )

    # Crear datos
    df = pd.DataFrame({
        'value': np.random.uniform(0, 100, len(timestamps)),
        'sensor_id': 'sensor_001'
    }, index=timestamps)

    # Crear gaps
    gap_size = int(len(df) * gap_percentage)
    gap_indices = np.random.choice(len(df), size=gap_size, replace=False)
    df = df.drop(df.index[gap_indices])

    return df


def create_large_dataframe(rows: int = 100000) -> pd.DataFrame:
    """
    Crea un DataFrame grande para tests de performance.

    Args:
        rows: Numero de filas (default: 100k)

    Returns:
        DataFrame grande
    """
    timestamps = pd.date_range(
        start='2024-01-01',
        periods=rows,
        freq='1s'
    )

    df = pd.DataFrame({
        'cpu_usage': np.random.uniform(0, 100, rows),
        'memory_usage': np.random.uniform(0, 100, rows),
        'disk_io': np.random.uniform(0, 1000, rows),
        'network_tx': np.random.uniform(0, 1000, rows),
        'network_rx': np.random.uniform(0, 1000, rows),
    }, index=timestamps)

    return df


def create_multivariate_dataframe(
    rows: int = 1000,
    num_sensors: int = 5,
) -> pd.DataFrame:
    """
    Crea un DataFrame con multiples sensores/variables.

    Args:
        rows: Numero de filas
        num_sensors: Numero de sensores

    Returns:
        DataFrame con datos de multiples sensores
    """
    timestamps = pd.date_range(
        start='2024-01-01',
        periods=rows,
        freq='1min'
    )

    data = {}
    for i in range(num_sensors):
        data[f'sensor_{i}_temp'] = np.random.uniform(15, 35, rows)
        data[f'sensor_{i}_hum'] = np.random.uniform(30, 70, rows)

    df = pd.DataFrame(data, index=timestamps)
    return df


# Datos de ejemplo para diferentes escenarios
SAMPLE_POINTS = [
    {
        "measurement": "temperature",
        "time": "2024-01-01T00:00:00Z",
        "fields": {"value": 25.5, "sensor_id": "001"},
        "tags": {"location": "room_1"},
    },
    {
        "measurement": "temperature",
        "time": "2024-01-01T00:01:00Z",
        "fields": {"value": 26.0, "sensor_id": "001"},
        "tags": {"location": "room_1"},
    },
    {
        "measurement": "temperature",
        "time": "2024-01-01T00:02:00Z",
        "fields": {"value": 25.8, "sensor_id": "001"},
        "tags": {"location": "room_1"},
    },
]

SAMPLE_TAGS = {
    "location": "lab_01",
    "environment": "production",
    "sensor_type": "DHT22",
}

SAMPLE_FIELDS = ["temperature", "humidity", "pressure"]
