#!/usr/bin/env python3
"""
Script de demostración rápida de las mejoras en InfluxdbOperation.

Este script muestra las características principales sin necesidad de tener
InfluxDB corriendo (usa mocking para simular las respuestas).
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock


def demo_normalize_values():
    """Demo: Normalización de valores."""
    print("\n" + "="*70)
    print("DEMO 1: Normalización de Valores")
    print("="*70)

    from ctrutils.database.influxdb import InfluxdbOperation

    # Crear con mock
    mock_client = Mock()
    mock_client._host = 'localhost'
    mock_client._port = 8086
    influx = InfluxdbOperation(client=mock_client)

    # Probar diferentes valores
    test_values = [
        (42, "Integer"),
        (42.5, "Float"),
        (np.nan, "NaN"),
        (np.inf, "Infinito"),
        (-np.inf, "-Infinito"),
        (None, "None"),
        (True, "Boolean True"),
        (False, "Boolean False"),
        ("texto", "String válido"),
        ("", "String vacío"),
        ("nan", "String 'nan'"),
        (np.int64(100), "Numpy int64"),
        (np.float64(3.14), "Numpy float64"),
    ]

    print("\nProbando normalización de valores:")
    print(f"{'Entrada':<20} {'Tipo':<20} {'Resultado':<20}")
    print("-" * 70)

    for value, desc in test_values:
        result = influx.normalize_value_to_write(value)
        result_str = str(result) if result is not None else "❌ None (eliminado)"
        print(f"{str(value):<20} {desc:<20} {result_str:<20}")


def demo_dataframe_with_nan():
    """Demo: DataFrame con NaN."""
    print("\n" + "="*70)
    print("DEMO 2: DataFrame con NaN Salteados")
    print("="*70)

    from ctrutils.database.influxdb import InfluxdbOperation

    # Crear DataFrame con NaN
    fechas = pd.date_range('2024-01-01', periods=10, freq='H')
    df = pd.DataFrame({
        'temperatura': [20.5, np.nan, 21.0, 22.5, np.nan, 23.0, np.inf, 24.0, 25.0, np.nan],
        'humedad': [45.0, 50.0, np.nan, 55.0, 60.0, np.nan, 65.0, np.inf, 70.0, 75.0],
        'presion': [1013, 1014, 1015, np.nan, 1016, 1017, 1018, 1019, np.nan, 1020]
    }, index=fechas)

    print("\n📊 DataFrame original:")
    print(df)

    print("\n📈 Estadísticas de NaN e infinitos:")
    for col in df.columns:
        nan_count = df[col].isna().sum()
        inf_count = np.isinf(df[col]).sum()
        print(f"  {col}:")
        print(f"    - NaN: {nan_count}")
        print(f"    - Infinitos: {inf_count}")
        print(f"    - Válidos: {len(df) - nan_count - inf_count}")

    # Mock de InfluxDB
    mock_client = Mock()
    mock_client._host = 'localhost'
    mock_client._port = 8086
    mock_client.get_list_database.return_value = [{'name': 'demo_db'}]
    mock_client.write_points.return_value = None

    influx = InfluxdbOperation(client=mock_client)

    # Simular escritura con validación
    print("\n✍️  Simulando escritura con validate_data=True...")
    stats = influx.write_dataframe(
        measurement='clima',
        data=df,
        database='demo_db',
        batch_size=5,
        validate_data=True
    )

    print("\n📊 Estadísticas de escritura:")
    print(f"  ✅ Total de puntos procesados: {stats['total_points']}")
    print(f"  ✅ Puntos escritos: {stats['written_points']}")
    print(f"  ❌ Puntos inválidos (eliminados): {stats['invalid_points']}")
    print(f"  📦 Número de lotes: {stats['batches']}")

    eficiencia = (stats['written_points'] / stats['total_points']) * 100
    print(f"\n  💯 Eficiencia: {eficiencia:.1f}%")


def demo_validate_point():
    """Demo: Validación de puntos."""
    print("\n" + "="*70)
    print("DEMO 3: Validación de Puntos")
    print("="*70)

    from ctrutils.database.influxdb import InfluxdbOperation

    mock_client = Mock()
    mock_client._host = 'localhost'
    mock_client._port = 8086
    influx = InfluxdbOperation(client=mock_client)

    # Diferentes casos de puntos
    test_points = [
        {
            'name': 'Punto válido completo',
            'point': {
                'measurement': 'test',
                'fields': {
                    'temp': 20.5,
                    'hum': 50.0,
                    'activo': True
                }
            }
        },
        {
            'name': 'Punto con algunos NaN',
            'point': {
                'measurement': 'test',
                'fields': {
                    'temp': 20.5,
                    'hum': np.nan,
                    'presion': 1013.0
                }
            }
        },
        {
            'name': 'Punto con infinitos',
            'point': {
                'measurement': 'test',
                'fields': {
                    'temp': np.inf,
                    'hum': -np.inf,
                    'presion': 1013.0
                }
            }
        },
        {
            'name': 'Punto con todos valores inválidos',
            'point': {
                'measurement': 'test',
                'fields': {
                    'temp': np.nan,
                    'hum': np.inf,
                    'presion': None
                }
            }
        },
        {
            'name': 'Punto vacío',
            'point': {
                'measurement': 'test',
                'fields': {}
            }
        }
    ]

    print("\nProbando validación de diferentes puntos:\n")

    for test in test_points:
        print(f"📍 {test['name']}:")
        print(f"   Entrada: {test['point']['fields']}")

        validated = influx._validate_point(test['point'])

        if validated is None:
            print(f"   Resultado: ❌ RECHAZADO (sin campos válidos)")
        else:
            print(f"   Resultado: ✅ ACEPTADO")
            print(f"   Campos válidos: {validated['fields']}")
        print()


def demo_large_dataframe_simulation():
    """Demo: Simulación de DataFrame grande."""
    print("\n" + "="*70)
    print("DEMO 4: Simulación de DataFrame Grande")
    print("="*70)

    from ctrutils.database.influxdb import InfluxdbOperation

    # Simular un DataFrame grande (100k filas)
    num_rows = 100_000
    print(f"\n📊 Creando DataFrame con {num_rows:,} filas...")

    fechas = pd.date_range('2024-01-01', periods=num_rows, freq='1min')
    df = pd.DataFrame({
        'sensor_1': np.random.normal(25, 3, num_rows),
        'sensor_2': np.random.normal(30, 5, num_rows),
        'sensor_3': np.random.normal(22, 2, num_rows),
    }, index=fechas)

    # Agregar 5% de NaN aleatorios
    print("   Agregando 5% de valores NaN aleatorios...")
    for col in df.columns:
        nan_indices = df.sample(frac=0.05).index
        df.loc[nan_indices, col] = np.nan

    # Agregar algunos infinitos
    print("   Agregando valores infinitos...")
    df.loc[df.sample(n=100).index, 'sensor_1'] = np.inf
    df.loc[df.sample(n=50).index, 'sensor_2'] = -np.inf

    print(f"\n📈 Estadísticas del DataFrame:")
    print(f"   Filas totales: {len(df):,}")
    print(f"   Columnas: {len(df.columns)}")

    total_values = len(df) * len(df.columns)
    nan_count = df.isna().sum().sum()
    inf_count = np.isinf(df.select_dtypes(include=[np.number])).sum().sum()
    valid_count = total_values - nan_count - inf_count

    print(f"   Valores totales: {total_values:,}")
    print(f"   Valores válidos: {valid_count:,}")
    print(f"   NaN: {nan_count:,} ({(nan_count/total_values*100):.1f}%)")
    print(f"   Infinitos: {inf_count:,} ({(inf_count/total_values*100):.1f}%)")

    # Mock de InfluxDB
    mock_client = Mock()
    mock_client._host = 'localhost'
    mock_client._port = 8086
    mock_client.get_list_database.return_value = [{'name': 'demo_db'}]
    mock_client.write_points.return_value = None

    influx = InfluxdbOperation(client=mock_client)

    # Simular escritura
    print("\n✍️  Simulando escritura con lotes de 10,000...")
    stats = influx.write_dataframe(
        measurement='sensores',
        data=df,
        database='demo_db',
        batch_size=10_000,
        validate_data=True
    )

    print("\n📊 Resultado de la escritura:")
    print(f"   Puntos procesados: {stats['total_points']:,}")
    print(f"   Puntos escritos: {stats['written_points']:,}")
    print(f"   Puntos rechazados: {stats['invalid_points']:,}")
    print(f"   Lotes procesados: {stats['batches']}")
    print(f"   Eficiencia: {(stats['written_points']/stats['total_points']*100):.1f}%")


def demo_administrative_operations():
    """Demo: Operaciones administrativas."""
    print("\n" + "="*70)
    print("DEMO 5: Operaciones Administrativas (Simuladas)")
    print("="*70)

    from ctrutils.database.influxdb import InfluxdbOperation

    # Mock de InfluxDB
    mock_client = Mock()
    mock_client._host = 'localhost'
    mock_client._port = 8086

    # Simular respuestas
    mock_client.get_list_database.return_value = [
        {'name': 'database_1'},
        {'name': 'database_2'},
        {'name': 'database_3'}
    ]

    mock_result = Mock()
    mock_result.get_points.return_value = [
        {'name': 'temperatura'},
        {'name': 'humedad'},
        {'name': 'presion'}
    ]
    mock_client.query.return_value = mock_result

    influx = InfluxdbOperation(client=mock_client)

    # Listar bases de datos
    print("\n📚 Bases de datos disponibles:")
    databases = influx.list_databases()
    for db in databases:
        print(f"   • {db}")

    # Verificar existencia
    print("\n🔍 Verificando existencia de bases de datos:")
    print(f"   ¿Existe 'database_1'? {'✅ Sí' if influx.database_exists('database_1') else '❌ No'}")
    print(f"   ¿Existe 'database_99'? {'✅ Sí' if influx.database_exists('database_99') else '❌ No'}")

    # Listar mediciones (simulado)
    print("\n📊 Mediciones en 'database_1':")
    measurements = influx.list_measurements('database_1')
    for measurement in measurements:
        print(f"   • {measurement}")


def main():
    """Ejecutar todas las demos."""
    print("\n")
    print("="*70)
    print(" DEMOSTRACIÓN DE MEJORAS EN InfluxdbOperation v11.0.0")
    print("="*70)
    print("\nEste script demuestra las nuevas funcionalidades sin necesidad")
    print("de tener InfluxDB corriendo (usa mocking para simular respuestas)")

    try:
        demo_normalize_values()
        demo_validate_point()
        demo_dataframe_with_nan()
        demo_large_dataframe_simulation()
        demo_administrative_operations()

        print("\n" + "="*70)
        print(" ✅ DEMOSTRACIÓN COMPLETADA")
        print("="*70)
        print("\nPara más ejemplos, ver:")
        print("  • examples/influxdb_usage_example.py")
        print("  • ctrutils/database/influxdb/README.md")
        print("  • CHANGELOG_INFLUXDB_v11.md")
        print()

    except Exception as e:
        print(f"\n❌ Error durante la demostración: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
