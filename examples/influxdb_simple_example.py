#!/usr/bin/env python3
"""
Ejemplo simple de uso del modulo InfluxDB de ctrutils.

Este ejemplo demuestra las operaciones basicas:
1. Conectar a InfluxDB
2. Escribir datos desde un DataFrame
3. Leer datos
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from ctrutils.database.influxdb import InfluxdbOperation

def main():
    # ========================================
    # 1. CONECTAR A INFLUXDB
    # ========================================
    print("1. Conectando a InfluxDB...")

    influx = InfluxdbOperation(
        host='localhost',
        port=8086,  # Puerto por defecto
    )

    # Crear y seleccionar base de datos
    database = 'mi_proyecto'
    if not influx.database_exists(database):
        influx.create_database(database)

    influx.switch_database(database)
    print(f"   Conectado a base de datos: {database}")

    # ========================================
    # 2. ESCRIBIR DATOS
    # ========================================
    print("\n2. Escribiendo datos...")

    # Crear un DataFrame con datos de sensores
    # IMPORTANTE: El indice debe ser DatetimeIndex
    timestamps = pd.date_range(
        start=datetime.now() - timedelta(hours=1),
        end=datetime.now(),
        freq='1min'
    )

    df = pd.DataFrame({
        'temperatura': np.random.uniform(20, 30, len(timestamps)),
        'humedad': np.random.uniform(40, 80, len(timestamps)),
        'presion': np.random.uniform(1000, 1020, len(timestamps)),
    }, index=timestamps)

    # Escribir el DataFrame a InfluxDB
    stats = influx.write_dataframe(
        measurement='clima',
        df=df,
        database=database,
        tags={'location': 'oficina', 'sensor': 'DHT22'},
        validate_data=True,           # Limpia NaN e infinitos
        convert_index_to_utc=True,    # Convierte timestamps a UTC
        batch_size=1000
    )

    print(f"   Escritos {stats['written_points']} puntos")
    print(f"   Puntos invalidos: {stats['invalid_points']}")

    # ========================================
    # 3. LEER DATOS
    # ========================================
    print("\n3. Leyendo datos...")

    # Opcion A: Leer ultimos N puntos
    df_last = influx.read_last_n_points(
        measurement='clima',
        n=10,
        database=database
    )
    print(f"   Ultimos 10 puntos:\n{df_last.head()}")

    # Opcion B: Leer rango de tiempo
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=30)

    df_range = influx.read_time_range(
        measurement='clima',
        start_time=start_time,
        end_time=end_time,
        database=database
    )
    print(f"\n   Puntos en ultimos 30 min: {len(df_range)}")

    # Opcion C: Query personalizada con filtros
    df_filtered = influx.query_to_dataframe(
        measurement='clima',
        fields=['temperatura', 'humedad'],  # Solo estos campos
        limit=20,
        database=database
    )
    print(f"\n   Temperatura promedio: {df_filtered['temperatura'].mean():.2f}")

    # ========================================
    # 4. INFORMACION DE LA BASE DE DATOS
    # ========================================
    print("\n4. Informacion de la base de datos...")

    measurements = influx.get_measurements(database)
    print(f"   Measurements: {measurements}")

    info = influx.get_measurement_info('clima', database)
    print(f"   Total de puntos: {info['point_count']}")
    print(f"   Tags: {info['tags']}")
    print(f"   Fields: {list(info['fields'].keys())}")

    print("\nEjemplo completado exitosamente!")

if __name__ == "__main__":
    main()
