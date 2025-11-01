"""
EJEMPLO ULTRA SIMPLE - InfluxdbOperation v11.0.0

Este es el ejemplo más simple posible para comenzar a usar
la clase InfluxdbOperation mejorada.
"""

import pandas as pd
import numpy as np
from ctrutils.database.influxdb import InfluxdbOperation

# ============================================================================
# EJEMPLO 1: Escribir DataFrame con NaN (EL CASO MÁS COMÚN)
# ============================================================================

# Crear conexión
influx = InfluxdbOperation(
    host='localhost',
    port=8086,
    username='admin',      # opcional
    password='password'    # opcional
)

# Cambiar a la base de datos
influx.switch_database('mi_db')

# Crear un DataFrame con valores NaN salteados
df = pd.DataFrame({
    'temperatura': [20.5, np.nan, 21.0, 22.5, np.nan],
    'humedad': [45.0, 50.0, np.nan, 55.0, 60.0]
}, index=pd.date_range('2024-01-01', periods=5, freq='H'))

print("DataFrame original:")
print(df)
print()

# Escribir con validación automática (¡esto es lo nuevo!)
stats = influx.write_dataframe(
    measurement='clima',
    data=df,
    validate_data=True,  # ← ¡Esto limpia los NaN automáticamente!
    tags={'sensor': 'sensor_01'}
)

# Ver estadísticas
print("Resultado:")
print(f"  ✅ Escritos: {stats['written_points']} puntos")
print(f"  ❌ Inválidos: {stats['invalid_points']} puntos")
print(f"  📦 Lotes: {stats['batches']}")
print()

# ============================================================================
# EJEMPLO 2: Explorar la base de datos
# ============================================================================

# Ver todas las bases de datos
print("Bases de datos disponibles:")
for db in influx.list_databases():
    print(f"  • {db}")
print()

# Ver mediciones en la base de datos actual
print("Mediciones en 'mi_db':")
for measurement in influx.list_measurements():
    print(f"  • {measurement}")
print()

# Ver información de una medición
info = influx.get_measurement_info('clima')
print(f"Información de 'clima':")
print(f"  Tags: {info['tags']}")
print(f"  Campos: {info['fields']}")
print(f"  Total de puntos: {info['point_count']}")
print()

# ============================================================================
# EJEMPLO 3: Leer datos
# ============================================================================

# Leer los últimos 10 puntos
df_leido = influx.get_data(
    query='SELECT * FROM "clima" ORDER BY time DESC LIMIT 10',
    database='mi_db'
)

print("Datos leídos:")
print(df_leido)
print()

# ============================================================================
# EJEMPLO 4: Contar puntos
# ============================================================================

total = influx.count_points('clima')
print(f"Total de puntos en 'clima': {total}")

# ============================================================================
# FIN - ¡Eso es todo!
# ============================================================================

print("\n✅ ¡Ejemplo completado!")
print("\nPara más ejemplos, ver:")
print("  • examples/influxdb_usage_example.py")
print("  • ctrutils/database/influxdb/README.md")
