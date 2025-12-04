# InfluxDB - Ejemplos Prácticos

## Tabla de Contenidos
1. [Escritura Básica](#escritura-básica)
2. [Lectura de Datos](#lectura-de-datos)
3. [Conversión de Timezone a UTC](#conversión-de-timezone-a-utc)
4. [Trabajar con Tags y Fields](#trabajar-con-tags-y-fields)
5. [Validación y Limpieza de Datos](#validación-y-limpieza-de-datos)
6. [Operaciones Avanzadas](#operaciones-avanzadas)

---

## Escritura Básica

### Ejemplo 1: Escribir DataFrame Simple

```python
from ctrutils.database.influxdb import InfluxdbOperation
import pandas as pd
from datetime import datetime, timedelta

# Conectar
influx = InfluxdbOperation(host='localhost', port=8086)
influx.switch_database('mi_db')

# Crear DataFrame
timestamps = pd.date_range(
    start=datetime.now() - timedelta(hours=1),
    periods=60,
    freq='1min'
)

df = pd.DataFrame({
    'temperatura': [20 + i*0.1 for i in range(60)],
    'humedad': [50 + i*0.5 for i in range(60)]
}, index=timestamps)

# Escribir
stats = influx.write_dataframe(
    measurement='clima',
    df=df,
    tags={'sensor': 'DHT22', 'location': 'oficina'}
)

print(f"Escritos {stats['written_points']}/{stats['total_points']} puntos")
```

### Ejemplo 2: Escribir Múltiples Series con Tags

```python
import numpy as np

# Datos de múltiples sensores
sensors = ['sensor_001', 'sensor_002', 'sensor_003']
timestamps = pd.date_range('2024-01-01', periods=100, freq='1min')

for sensor_id in sensors:
    df = pd.DataFrame({
        'temperatura': np.random.uniform(18, 28, 100),
        'humedad': np.random.uniform(40, 80, 100),
    }, index=timestamps)

    influx.write_dataframe(
        measurement='sensores',
        df=df,
        tags={'sensor_id': sensor_id, 'location': 'planta_1'},
        convert_index_to_utc=True
    )
    print(f"Escritos datos de {sensor_id}")
```

### Ejemplo 3: Escribir con Columnas como Tags

```python
# DataFrame con columna que será tag
df = pd.DataFrame({
    'sensor_id': ['DHT22'] * 100,  # Esta será un tag
    'temperatura': np.random.uniform(20, 30, 100),
    'humedad': np.random.uniform(40, 80, 100),
}, index=pd.date_range('2024-01-01', periods=100, freq='1min'))

# Usar la columna como tag
influx.write_dataframe(
    measurement='clima',
    df=df,
    tag_columns=['sensor_id'],  # Columna sensor_id se usa como tag
    field_columns=['temperatura', 'humedad']  # Solo estos como fields
)
```

---

## Lectura de Datos

### Ejemplo 4: Leer Últimos Puntos

```python
# Leer últimos 50 puntos
df = influx.read_last_n_points(
    measurement='clima',
    n=50
)

print(df.head())
print(f"\nTotal puntos: {len(df)}")
print(f"Columnas: {list(df.columns)}")
print(f"Rango: {df.index.min()} a {df.index.max()}")
```

### Ejemplo 5: Leer Rango de Tiempo

```python
from datetime import datetime, timedelta

# Leer últimas 24 horas
end_time = datetime.now()
start_time = end_time - timedelta(hours=24)

df = influx.read_time_range(
    measurement='clima',
    start_time=start_time,
    end_time=end_time
)

# Calcular estadísticas
print(f"Temperatura promedio: {df['temperatura'].mean():.2f}°C")
print(f"Temperatura máxima: {df['temperatura'].max():.2f}°C")
print(f"Temperatura mínima: {df['temperatura'].min():.2f}°C")
```

### Ejemplo 6: Query con Filtros Complejos

```python
# Leer solo campos específicos con filtros
df = influx.query_to_dataframe(
    measurement='sensores',
    fields=['temperatura', 'humedad'],
    start_time='2024-01-01T00:00:00Z',
    end_time='2024-01-31T23:59:59Z',
    where_conditions={'sensor_id': 'DHT22', 'location': 'oficina'},
    limit=5000
)

# Filtrar temperaturas altas
high_temp = df[df['temperatura'] > 25]
print(f"Registros con temperatura alta: {len(high_temp)}")
```

---

## Conversión de Timezone a UTC

### Ejemplo 7: Escribir desde Timezone Local

```python
# DataFrame con timezone de Madrid
timestamps = pd.date_range(
    start='2024-01-01',
    periods=100,
    freq='1h',
    tz='Europe/Madrid'  # Timezone local
)

df = pd.DataFrame({
    'temperatura': np.random.uniform(15, 25, 100)
}, index=timestamps)

print(f"Timezone original: {df.index.tz}")

# Se convierte automáticamente a UTC al escribir
stats = influx.write_dataframe(
    measurement='temperatura_madrid',
    df=df,
    convert_index_to_utc=True  # Convierte Europe/Madrid -> UTC
)

# Leer y verificar
df_read = influx.read_last_n_points('temperatura_madrid', n=5)
print(f"Timezone en InfluxDB: {df_read.index.tz}")  # UTC
```

### Ejemplo 8: Manejar Timestamps sin Timezone

```python
# DataFrame sin timezone (naive)
timestamps = pd.date_range('2024-01-01', periods=100, freq='1h')
df = pd.DataFrame({
    'valor': np.random.uniform(0, 100, 100)
}, index=timestamps)

print(f"Timezone original: {df.index.tz}")  # None

# Se asume UTC al escribir
influx.write_dataframe(
    measurement='datos',
    df=df,
    convert_index_to_utc=True  # Localiza como UTC
)
```

### Ejemplo 9: Leer y Convertir a Timezone Local

```python
# Leer datos (están en UTC)
df = influx.read_last_n_points('temperatura', n=100)
print(f"Timezone desde InfluxDB: {df.index.tz}")  # UTC

# Convertir a timezone local
df_local = df.copy()
df_local.index = df_local.index.tz_convert('Europe/Madrid')
print(f"Timezone convertida: {df_local.index.tz}")  # Europe/Madrid

# O usar el parámetro directo
df_local = influx.query_to_dataframe(
    measurement='temperatura',
    limit=100,
    convert_to_local_tz=True  # Convierte automáticamente
)
```

---

## Trabajar con Tags y Fields

### Ejemplo 10: Consultar Estructura del Measurement

```python
# Ver información completa
info = influx.get_measurement_info('sensores', 'mi_db')

print(f"Measurement: {info['name']}")
print(f"Tags disponibles: {info['tags']}")
print(f"Fields disponibles: {info['fields']}")
print(f"Total de series: {info['cardinality']}")
print(f"Total de puntos: {info['point_count']}")

# Ver valores únicos de un tag
sensor_ids = influx.list_tag_values('sensores', 'sensor_id')
print(f"Sensores registrados: {sensor_ids}")
```

### Ejemplo 11: Filtrar por Tags

```python
# Leer solo de un sensor específico
df = influx.query_to_dataframe(
    measurement='sensores',
    where_conditions={'sensor_id': 'DHT22'},
    limit=1000
)

print(f"Datos del sensor DHT22: {len(df)} puntos")

# Leer comparando múltiples sensores
for sensor_id in ['sensor_001', 'sensor_002']:
    df = influx.query_to_dataframe(
        measurement='sensores',
        fields=['temperatura'],
        where_conditions={'sensor_id': sensor_id},
        limit=100
    )
    print(f"{sensor_id}: Temp promedio = {df['temperatura'].mean():.2f}°C")
```

---

## Validación y Limpieza de Datos

### Ejemplo 12: Manejo Automático de NaN

```python
# DataFrame con NaN
df = pd.DataFrame({
    'temperatura': [20.0, np.nan, 22.0, np.nan, 24.0],
    'humedad': [50.0, 55.0, np.nan, 60.0, 65.0]
}, index=pd.date_range('2024-01-01', periods=5, freq='1h'))

print("DataFrame original:")
print(df)

# Escribir con validación (NaN se eliminan automáticamente)
stats = influx.write_dataframe(
    measurement='clima',
    df=df,
    validate_data=True  # Limpia NaN
)

print(f"\nPuntos válidos escritos: {stats['written_points']}")
print(f"Puntos inválidos: {stats['invalid_points']}")

# Leer y verificar
df_read = influx.read_last_n_points('clima', n=5)
print("\nDataFrame leído (sin NaN):")
print(df_read)
```

### Ejemplo 13: Validación Manual

```python
# Validar valores antes de escribir
df = pd.DataFrame({
    'temperatura': [20.0, np.inf, 22.0, -np.inf, 24.0, np.nan],
    'humedad': [50.0, 55.0, 60.0, 65.0, 70.0, 75.0]
}, index=pd.date_range('2024-01-01', periods=6, freq='1h'))

# Verificar valores problemáticos
print("Valores infinitos en temperatura:", df['temperatura'].isin([np.inf, -np.inf]).sum())
print("Valores NaN en temperatura:", df['temperatura'].isna().sum())

# Escribir (se limpian automáticamente)
stats = influx.write_dataframe(
    measurement='test_validacion',
    df=df,
    validate_data=True
)

print(f"De {stats['total_points']} puntos, {stats['written_points']} son válidos")
```

---

## Operaciones Avanzadas

### Ejemplo 14: Calcular Métricas de Calidad

```python
# Escribir datos de ejemplo
df = pd.DataFrame({
    'temperatura': np.random.normal(25, 5, 1000),  # Media 25, std 5
    'humedad': np.random.uniform(40, 80, 1000)
}, index=pd.date_range('2024-01-01', periods=1000, freq='1h'))

# Agregar algunos outliers
df.loc[df.index[10:15], 'temperatura'] = 100  # Outliers
df.loc[df.index[20:25], 'temperatura'] = np.nan  # Missing

influx.write_dataframe(measurement='calidad_test', df=df)

# Calcular métricas de calidad
metrics = influx.calculate_data_quality_metrics('calidad_test')

for field, stats in metrics.items():
    print(f"\n{field}:")
    print(f"  Total valores: {stats['count']}")
    print(f"  Valores faltantes: {stats['missing']} ({stats['missing_percentage']:.1f}%)")
    print(f"  Media: {stats['mean']:.2f}")
    print(f"  Desv. estándar: {stats['std']:.2f}")
    print(f"  Outliers detectados: {stats['outliers']}")
```

### Ejemplo 15: Downsample de Datos

```python
# Datos en alta frecuencia (1 minuto)
timestamps = pd.date_range('2024-01-01', periods=1440, freq='1min')
df = pd.DataFrame({
    'temperatura': np.random.normal(25, 2, 1440),
    'humedad': np.random.normal(60, 10, 1440)
}, index=timestamps)

influx.write_dataframe(measurement='raw_data', df=df)

# Crear versión agregada por hora
points_created = influx.downsample_data(
    measurement='raw_data',
    target_measurement='hourly_avg',
    aggregation_window='1h',
    aggregation_func='MEAN',
    fields=['temperatura', 'humedad']
)

print(f"Puntos agregados creados: {points_created}")

# Comparar tamaños
raw_count = influx.count_points('raw_data')
agg_count = influx.count_points('hourly_avg')
print(f"Raw data: {raw_count} puntos")
print(f"Aggregated: {agg_count} puntos")
print(f"Reducción: {(1 - agg_count/raw_count)*100:.1f}%")
```

### Ejemplo 16: Backup y Restore

```python
import tempfile
import os

# Backup de measurement
with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
    backup_file = f.name

# Exportar a CSV
points_exported = influx.backup_measurement(
    measurement='temperatura',
    output_file=backup_file,
    start_time='2024-01-01T00:00:00Z'
)

print(f"Backup completado: {points_exported} puntos exportados")
print(f"Archivo: {backup_file}")

# Restaurar en otro measurement
stats = influx.restore_measurement(
    measurement='temperatura_restored',
    input_file=backup_file,
    tags={'backup': 'true'}
)

print(f"Restore completado: {stats['written_points']} puntos")

# Limpiar archivo temporal
os.remove(backup_file)
```

### Ejemplo 17: Usar Transaction Context

```python
# Operación transaccional
try:
    with influx.transaction('mi_db'):
        # Escribir múltiples measurements
        influx.write_dataframe(measurement='temp', df=df_temp)
        influx.write_dataframe(measurement='humidity', df=df_humid)
        influx.write_dataframe(measurement='pressure', df=df_press)
        print("Todas las escrituras completadas")
except Exception as e:
    print(f"Error en transacción: {e}")
```

### Ejemplo 18: Monitoreo con Métricas

```python
# Activar logging y métricas
influx.enable_logging()
influx.reset_metrics()

# Realizar múltiples operaciones
for i in range(10):
    df = pd.DataFrame({
        'value': np.random.uniform(0, 100, 100)
    }, index=pd.date_range('2024-01-01', periods=100, freq='1min'))

    influx.write_dataframe(measurement='test_metrics', df=df)

# Ver métricas de rendimiento
metrics = influx.get_metrics()
print("\nMétricas de Rendimiento:")
print(f"  Total escrituras: {metrics['total_writes']}")
print(f"  Total puntos: {metrics['total_points']}")
print(f"  Escrituras fallidas: {metrics['failed_writes']}")
print(f"  Tiempo promedio: {metrics['avg_write_time']:.3f}s")
print(f"  Tasa de éxito: {metrics['success_rate']:.1f}%")
```

---

## Casos de Uso Reales

### Ejemplo 19: Monitor de Servidor

```python
import psutil
from datetime import datetime, timezone

def monitor_server(influx, duration_minutes=60):
    """Monitorea métricas del servidor y las guarda en InfluxDB."""

    influx.switch_database('monitoring')

    for i in range(duration_minutes):
        # Recolectar métricas
        timestamp = datetime.now(tz=timezone.utc)

        metrics = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
        }

        # Escribir punto
        point = {
            "measurement": "server_metrics",
            "time": timestamp,
            "tags": {"hostname": "server01"},
            "fields": metrics
        }

        influx.write_points([point])
        print(f"{timestamp}: CPU={metrics['cpu_percent']:.1f}%")

        time.sleep(60)  # Esperar 1 minuto

# Usar
# monitor_server(influx, duration_minutes=60)
```

### Ejemplo 20: Análisis de Series Temporales

```python
# Leer datos históricos
df = influx.read_time_range(
    measurement='temperatura',
    start_time=datetime.now() - timedelta(days=30),
    end_time=datetime.now()
)

# Análisis estadístico
print("Análisis de 30 días:")
print(f"  Puntos totales: {len(df)}")
print(f"  Temperatura media: {df['temperatura'].mean():.2f}°C")
print(f"  Desviación estándar: {df['temperatura'].std():.2f}°C")
print(f"  Temperatura máxima: {df['temperatura'].max():.2f}°C")
print(f"  Temperatura mínima: {df['temperatura'].min():.2f}°C")

# Resamplear a diario
df_daily = df['temperatura'].resample('1D').agg(['mean', 'min', 'max'])
print("\nPromedios diarios:")
print(df_daily.tail())

# Detectar anomalías (valores > 3 std)
mean = df['temperatura'].mean()
std = df['temperatura'].std()
anomalies = df[abs(df['temperatura'] - mean) > 3 * std]
print(f"\nAnomalías detectadas: {len(anomalies)}")
```

---

Ver también:
- [API Reference](INFLUXDB_API_REFERENCE.md)
- [Guía de Uso](INFLUXDB_USAGE.md)
