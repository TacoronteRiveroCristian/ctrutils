# InfluxDB Module - Guía de Uso

Módulo simplificado para trabajar con InfluxDB en Python usando pandas DataFrames.

## Características

- Escritura y lectura simplificada de DataFrames
- Conversión automática de timestamps a UTC
- Validación y limpieza de datos (NaN, infinitos)
- Métodos helper para operaciones comunes
- Soporte para tags y fields personalizados
- Escritura por lotes eficiente

## Instalación

```bash
pip install ctrutils[influxdb]
# o con poetry
poetry add ctrutils --extras influxdb
```

## Uso Básico

### 1. Conectar a InfluxDB

```python
from ctrutils.database.influxdb import InfluxdbOperation

# Crear instancia
influx = InfluxdbOperation(host='localhost', port=8086)

# Crear/seleccionar base de datos
influx.create_database('mi_db')
influx.switch_database('mi_db')
```

### 2. Escribir Datos

#### Desde DataFrame

```python
import pandas as pd
from datetime import datetime, timedelta

# Crear DataFrame con timestamps
timestamps = pd.date_range(
    start=datetime.now() - timedelta(hours=1),
    end=datetime.now(),
    freq='1min'
)

df = pd.DataFrame({
    'temperatura': [20.5, 21.0, 22.5, ...],
    'humedad': [45.0, 50.0, 55.0, ...],
}, index=timestamps)

# Escribir a InfluxDB
stats = influx.write_dataframe(
    measurement='clima',
    df=df,
    tags={'location': 'oficina', 'sensor': 'DHT22'},
    validate_data=True,           # Limpiar NaN/infinitos
    convert_index_to_utc=True,    # Convertir a UTC (recomendado)
    batch_size=1000
)

print(f"Escritos {stats['written_points']} puntos")
```

#### Escribir Puntos Directamente

```python
from datetime import timezone

points = [
    {
        "measurement": "temperatura",
        "time": datetime.now(tz=timezone.utc),
        "tags": {"sensor": "001"},
        "fields": {"value": 25.5, "unit": "celsius"}
    }
]

stats = influx.write_points(points, database='mi_db')
```

### 3. Leer Datos

#### Últimos N puntos

```python
# Leer últimos 100 puntos
df = influx.read_last_n_points(
    measurement='clima',
    n=100,
    database='mi_db'
)
```

#### Rango de tiempo

```python
from datetime import datetime, timedelta

# Leer última hora
end_time = datetime.now()
start_time = end_time - timedelta(hours=1)

df = influx.read_time_range(
    measurement='clima',
    start_time=start_time,
    end_time=end_time,
    database='mi_db'
)
```

#### Query personalizada

```python
# Con filtros y límites
df = influx.query_to_dataframe(
    measurement='clima',
    fields=['temperatura', 'humedad'],  # Solo estos campos
    start_time='2024-01-01T00:00:00Z',
    end_time='2024-01-31T23:59:59Z',
    where_conditions={'sensor': 'DHT22'},
    limit=1000,
    database='mi_db'
)
```

## Conversión a UTC

**IMPORTANTE**: Se recomienda siempre usar `convert_index_to_utc=True` al escribir datos.

```python
# Sin timezone (naive datetime) - se asume UTC
df = pd.DataFrame(..., index=pd.date_range(...))

# Con timezone local - se convierte a UTC
df = pd.DataFrame(..., index=pd.date_range(..., tz='Europe/Madrid'))

# En ambos casos, usar convert_index_to_utc=True
influx.write_dataframe(
    measurement='datos',
    df=df,
    convert_index_to_utc=True  # Garantiza que se escriba en UTC
)
```

## Validación de Datos

El módulo limpia automáticamente:
- Valores `NaN`
- Valores infinitos (`inf`, `-inf`)
- Valores `None`
- Strings vacíos o especiales ('nan', 'NaN', 'None', 'null')

```python
# DataFrame con valores problemáticos
df = pd.DataFrame({
    'valor': [1.0, np.nan, np.inf, 5.0, None, -np.inf],
}, index=pd.date_range('2024-01-01', periods=6, freq='1h'))

# Se escribirán solo los valores válidos (1.0, 5.0)
stats = influx.write_dataframe(
    measurement='test',
    df=df,
    validate_data=True  # Activado por defecto
)
```

## Información de Base de Datos

```python
# Listar bases de datos
databases = influx.get_databases()

# Listar measurements
measurements = influx.get_measurements('mi_db')

# Información detallada de un measurement
info = influx.get_measurement_info('clima', 'mi_db')
print(f"Tags: {info['tags']}")
print(f"Fields: {info['fields']}")
print(f"Total puntos: {info['point_count']}")
```

## Logging

```python
import logging

# Activar logging
influx.enable_logging(level=logging.DEBUG)

# O usar un logger personalizado
from ctrutils.handler import LoggingHandler

handler = LoggingHandler()
custom_logger = handler.add_handlers([
    handler.create_stream_handler(),
    handler.create_file_handler('influxdb.log')
])

influx.enable_logging(logger=custom_logger)
```

## Ejemplos Completos

Ver:
- `examples/influxdb_simple_example.py` - Ejemplo básico
- `test_influxdb_real.py` - Test completo con datos reales

## Tips y Mejores Prácticas

1. **Siempre usar UTC**: Configura `convert_index_to_utc=True` para evitar problemas de timezone.

2. **Batch size apropiado**:
   - DataFrames pequeños (<1000 filas): `batch_size=1000`
   - DataFrames grandes (>10000 filas): `batch_size=5000`

3. **Validación de datos**: Mantén `validate_data=True` para producción.

4. **Tags vs Fields**:
   - Tags: Metadatos para filtrar (sensor_id, location)
   - Fields: Valores numéricos/mediciones (temperatura, humedad)

5. **Nombres de measurements**: Usa nombres descriptivos y consistentes.

6. **Gestión de conexiones**: Reutiliza la instancia de `InfluxdbOperation`.

## Solución de Problemas

### Error de conexión

```python
# Verificar que InfluxDB esté corriendo
curl -I http://localhost:8086/ping

# Probar conexión
try:
    influx = InfluxdbOperation(host='localhost', port=8086)
    databases = influx.get_databases()
    print("Conexión exitosa!")
except Exception as e:
    print(f"Error: {e}")
```

### DataFrame sin DatetimeIndex

```python
# Convertir columna a índice datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
```

### Problemas con timezone

```python
# Verificar timezone del DataFrame
print(df.index.tz)

# Localizar si es naive
if df.index.tz is None:
    df.index = df.index.tz_localize('UTC')

# Convertir a UTC
df.index = df.index.tz_convert('UTC')
```

## Referencias

- [InfluxDB Python Client](https://github.com/influxdata/influxdb-python)
- [Pandas DatetimeIndex](https://pandas.pydata.org/docs/reference/api/pandas.DatetimeIndex.html)
