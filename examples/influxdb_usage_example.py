"""
Ejemplos de uso de la clase InfluxdbOperation mejorada.

Este archivo muestra cómo usar las nuevas funcionalidades de la clase InfluxdbOperation,
incluyendo validación de datos, limpieza de NaN, escritura por lotes, y operaciones administrativas.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ctrutils.database.influxdb import InfluxdbOperation


def ejemplo_1_crear_instancia():
    """Ejemplo 1: Diferentes formas de crear una instancia."""

    # Opción 1: Crear instancia con credenciales
    influx = InfluxdbOperation(
        host='localhost',
        port=8086,
        username='admin',
        password='password',
        timeout=10
    )

    # Opción 2: Usar un cliente existente
    from influxdb import InfluxDBClient
    client = InfluxDBClient(host='localhost', port=8086, username='admin', password='password')
    influx = InfluxdbOperation(client=client)

    return influx


def ejemplo_2_listar_bases_de_datos():
    """Ejemplo 2: Listar y gestionar bases de datos."""

    influx = InfluxdbOperation(host='localhost', port=8086)

    # Listar todas las bases de datos
    databases = influx.list_databases()
    print("Bases de datos disponibles:", databases)

    # Verificar si existe una base de datos
    if influx.database_exists('mi_db'):
        print("La base de datos 'mi_db' existe")
    else:
        # Crear la base de datos si no existe
        influx.create_database('mi_db')
        print("Base de datos 'mi_db' creada")

    # Cambiar a la base de datos
    influx.switch_database('mi_db')

    # Obtener información completa de la base de datos
    info = influx.get_database_info('mi_db')
    print(f"\nInformación de la base de datos:")
    print(f"  Nombre: {info['name']}")
    print(f"  Mediciones: {info['measurements']}")
    print(f"  Políticas de retención: {len(info['retention_policies'])}")


def ejemplo_3_escribir_dataframe_con_nan():
    """Ejemplo 3: Escribir DataFrame con valores NaN."""

    influx = InfluxdbOperation(host='localhost', port=8086)
    influx.switch_database('mi_db')

    # Crear un DataFrame con valores NaN salteados
    fechas = pd.date_range(start='2024-01-01', periods=100, freq='H')
    df = pd.DataFrame({
        'temperatura': np.random.normal(20, 5, 100),
        'humedad': np.random.normal(50, 10, 100),
        'presion': np.random.normal(1013, 5, 100),
    }, index=fechas)

    # Agregar algunos NaN aleatorios
    df.loc[df.sample(frac=0.2).index, 'temperatura'] = np.nan
    df.loc[df.sample(frac=0.15).index, 'humedad'] = np.nan
    df.loc[df.sample(frac=0.1).index, 'presion'] = np.nan

    # Agregar valores infinitos (que serán limpiados automáticamente)
    df.loc[df.sample(n=5).index, 'temperatura'] = np.inf
    df.loc[df.sample(n=3).index, 'humedad'] = -np.inf

    print(f"\nDataFrame original:")
    print(f"  Filas: {len(df)}")
    print(f"  NaN en temperatura: {df['temperatura'].isna().sum()}")
    print(f"  NaN en humedad: {df['humedad'].isna().sum()}")
    print(f"  Infinitos en temperatura: {np.isinf(df['temperatura']).sum()}")

    # Escribir el DataFrame con validación automática
    stats = influx.write_dataframe(
        measurement='clima',
        data=df,
        database='mi_db',
        batch_size=1000,
        validate_data=True,  # Activa la validación y limpieza
        tags={'sensor': 'sensor_01', 'location': 'oficina'}
    )

    print(f"\nEstadísticas de escritura:")
    print(f"  Total de puntos procesados: {stats['total_points']}")
    print(f"  Puntos escritos exitosamente: {stats['written_points']}")
    print(f"  Puntos inválidos (eliminados): {stats['invalid_points']}")
    print(f"  Número de lotes: {stats['batches']}")


def ejemplo_4_dataframe_muy_grande():
    """Ejemplo 4: Escribir un DataFrame muy grande con escritura por lotes."""

    influx = InfluxdbOperation(host='localhost', port=8086)
    influx.switch_database('mi_db')

    # Crear un DataFrame grande (por ejemplo, 1 año de datos cada minuto)
    fechas = pd.date_range(start='2023-01-01', end='2024-01-01', freq='1min')
    num_rows = len(fechas)

    print(f"\nCreando DataFrame con {num_rows:,} filas...")

    df = pd.DataFrame({
        'sensor_1': np.random.normal(25, 3, num_rows),
        'sensor_2': np.random.normal(30, 5, num_rows),
        'sensor_3': np.random.normal(22, 2, num_rows),
        'sensor_4': np.random.normal(28, 4, num_rows),
    }, index=fechas)

    # Agregar NaN aleatorios (5% de los datos)
    for col in df.columns:
        df.loc[df.sample(frac=0.05).index, col] = np.nan

    print(f"Escribiendo {num_rows:,} puntos en InfluxDB...")

    # Escribir con lotes pequeños para mejor rendimiento
    stats = influx.write_dataframe(
        measurement='sensores_continuos',
        data=df,
        database='mi_db',
        batch_size=5000,  # Lotes de 5000 puntos
        validate_data=True,
        drop_na_rows=False,  # No eliminar filas, solo valores individuales NaN
    )

    print(f"\nEscritura completada:")
    print(f"  Puntos escritos: {stats['written_points']:,}")
    print(f"  Tiempo estimado por lote: {stats['batches']} lotes")
    print(f"  Eficiencia: {(stats['written_points']/stats['total_points']*100):.1f}%")


def ejemplo_5_listar_mediciones_y_campos():
    """Ejemplo 5: Explorar mediciones, campos y tags."""

    influx = InfluxdbOperation(host='localhost', port=8086)
    influx.switch_database('mi_db')

    # Listar todas las mediciones
    measurements = influx.list_measurements('mi_db')
    print(f"\nMediciones en 'mi_db': {measurements}")

    # Para cada medición, obtener información detallada
    for measurement in measurements[:3]:  # Solo las primeras 3
        print(f"\n{'='*60}")
        print(f"Medición: {measurement}")
        print(f"{'='*60}")

        # Obtener información completa
        info = influx.get_measurement_info(measurement, 'mi_db')

        print(f"  Tags: {info['tags']}")
        print(f"  Campos:")
        for field, field_type in info['fields'].items():
            print(f"    - {field}: {field_type}")
        print(f"  Cardinalidad (series únicas): {info['cardinality']}")
        print(f"  Total de puntos: {info['point_count']:,}")

        # Obtener valores de un tag específico
        if info['tags']:
            tag = info['tags'][0]
            values = influx.list_tag_values(measurement, tag, 'mi_db')
            print(f"  Valores del tag '{tag}': {values}")


def ejemplo_6_escribir_puntos_directamente():
    """Ejemplo 6: Escribir puntos directamente (lista de diccionarios)."""

    influx = InfluxdbOperation(host='localhost', port=8086)
    influx.switch_database('mi_db')

    # Crear una lista de puntos manualmente
    now = datetime.utcnow()
    points = []

    for i in range(100):
        point = {
            "measurement": "eventos",
            "time": now - timedelta(hours=i),
            "tags": {
                "tipo": "tipo_A" if i % 2 == 0 else "tipo_B",
                "prioridad": "alta" if i % 3 == 0 else "baja"
            },
            "fields": {
                "valor": float(i * 10),
                "contador": float(i),
                "activo": True if i % 2 == 0 else False
            }
        }

        # Agregar algunos valores NaN que serán filtrados automáticamente
        if i % 7 == 0:
            point["fields"]["valor"] = np.nan

        points.append(point)

    # Escribir los puntos con validación
    stats = influx.write_points(
        points=points,
        database='mi_db',
        batch_size=50,
        validate_data=True
    )

    print(f"\nEscritura de puntos directa:")
    print(f"  Total: {stats['total_points']}")
    print(f"  Escritos: {stats['written_points']}")
    print(f"  Inválidos: {stats['invalid_points']}")


def ejemplo_7_contar_puntos():
    """Ejemplo 7: Contar puntos en una medición."""

    influx = InfluxdbOperation(host='localhost', port=8086)
    influx.switch_database('mi_db')

    # Contar todos los puntos
    total = influx.count_points('clima', 'mi_db')
    print(f"\nTotal de puntos en 'clima': {total:,}")

    # Contar puntos en un rango de tiempo
    total_enero = influx.count_points(
        'clima',
        'mi_db',
        start_time='2024-01-01T00:00:00Z',
        end_time='2024-01-31T23:59:59Z'
    )
    print(f"Puntos en enero 2024: {total_enero:,}")


def ejemplo_8_leer_datos():
    """Ejemplo 8: Leer datos con get_data."""

    influx = InfluxdbOperation(host='localhost', port=8086)

    # Leer los últimos 100 puntos
    query = 'SELECT * FROM "clima" ORDER BY time DESC LIMIT 100'
    df = influx.get_data(query, database='mi_db')

    print(f"\nDatos leídos:")
    print(f"  Filas: {len(df)}")
    print(f"  Columnas: {list(df.columns)}")
    print(f"\nPrimeras 5 filas:")
    print(df.head())

    # Estadísticas básicas
    print(f"\nEstadísticas:")
    print(df.describe())


def ejemplo_9_eliminar_datos():
    """Ejemplo 9: Eliminar datos de una medición."""

    influx = InfluxdbOperation(host='localhost', port=8086)
    influx.switch_database('mi_db')

    # Eliminar datos antiguos (más de 1 año)
    influx.delete(
        measurement='clima',
        end_time='2023-01-01T00:00:00Z',
        database='mi_db'
    )
    print("Datos antiguos eliminados")

    # Eliminar datos con filtros
    influx.delete(
        measurement='clima',
        filters={'sensor': 'sensor_viejo'},
        database='mi_db'
    )
    print("Datos del sensor viejo eliminados")


def ejemplo_10_gestionar_mediciones():
    """Ejemplo 10: Gestionar mediciones."""

    influx = InfluxdbOperation(host='localhost', port=8086)
    influx.switch_database('mi_db')

    # Verificar si existe una medición
    if influx.measurement_exists('medicion_vieja', 'mi_db'):
        print("La medición existe, eliminándola...")
        # Eliminar la medición completa
        influx.drop_measurement('medicion_vieja', 'mi_db', confirm=True)
        print("Medición eliminada")

    # Listar todas las mediciones después de eliminar
    measurements = influx.list_measurements('mi_db')
    print(f"Mediciones restantes: {measurements}")


if __name__ == "__main__":
    print("="*60)
    print("EJEMPLOS DE USO - InfluxdbOperation")
    print("="*60)

    # Descomentar los ejemplos que quieras ejecutar

    # ejemplo_1_crear_instancia()
    # ejemplo_2_listar_bases_de_datos()
    # ejemplo_3_escribir_dataframe_con_nan()
    # ejemplo_4_dataframe_muy_grande()
    # ejemplo_5_listar_mediciones_y_campos()
    # ejemplo_6_escribir_puntos_directamente()
    # ejemplo_7_contar_puntos()
    # ejemplo_8_leer_datos()
    # ejemplo_9_eliminar_datos()
    # ejemplo_10_gestionar_mediciones()

    print("\n" + "="*60)
    print("Descomenta los ejemplos en el main para ejecutarlos")
    print("="*60)
