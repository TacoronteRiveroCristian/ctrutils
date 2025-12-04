# InfluxDB Module - API Reference

## Clase: `InfluxdbOperation`

**Total de métodos públicos**: 43

---

## 📊 CONEXIÓN Y CONFIGURACIÓN

### `__init__(host, port, timeout=5, client=None, **kwargs)`
Inicializa la conexión a InfluxDB.
```python
influx = InfluxdbOperation(host='localhost', port=8086)
# O con cliente existente
influx = InfluxdbOperation(client=my_client)
```

### `switch_database(database: str)`
Cambia la base de datos activa.
```python
influx.switch_database('mi_db')
```

### `enable_logging(level=logging.INFO, logger=None)`
Activa el logging para debugging.
```python
influx.enable_logging(level=logging.DEBUG)
```

### `close_client()`
Cierra la conexión con InfluxDB.

### `get_client` (property)
Obtiene el cliente InfluxDBClient actual.

### `get_client_info` (property)
Obtiene información del cliente (host, port, database, etc.).

---

## ✍️ ESCRITURA DE DATOS

### `write_dataframe(measurement, df=None, data=None, **kwargs)`
**Método principal para escribir DataFrames.**

**Parámetros importantes**:
- `measurement`: Nombre del measurement
- `df` o `data`: DataFrame con índice DatetimeIndex
- `tags`: Dict con tags adicionales
- `database`: Base de datos (opcional)
- `batch_size`: Tamaño de lote (default: 1000)
- `validate_data`: Limpiar NaN/infinitos (default: True)
- `convert_index_to_utc`: Convertir a UTC (default: True) ⭐ **NUEVO**
- `field_columns`: Lista de columnas para fields
- `tag_columns`: Lista de columnas para tags

**Retorna**: Dict con estadísticas `{'total_points', 'written_points', 'invalid_points', 'batches'}`

```python
stats = influx.write_dataframe(
    measurement='temperatura',
    df=df,
    tags={'sensor': 'DHT22'},
    convert_index_to_utc=True  # Garantiza UTC
)
```

### `write_points(points, database=None, tags=None, batch_size=5000, validate_data=True)`
Escribe una lista de puntos directamente.

```python
points = [
    {
        "measurement": "temp",
        "time": datetime.now(tz=timezone.utc),
        "tags": {"sensor": "001"},
        "fields": {"value": 25.5}
    }
]
influx.write_points(points)
```

### `write_dataframe_parallel(df, measurement, max_workers=4, **kwargs)`
Escritura paralela para DataFrames grandes.

---

## 📖 LECTURA DE DATOS

### `query_to_dataframe(measurement, fields=None, start_time=None, end_time=None, **kwargs)` ⭐ **NUEVO**
**Método principal para leer datos.**

**Parámetros**:
- `measurement`: Nombre del measurement
- `fields`: Lista de campos (None = todos)
- `start_time`: Tiempo inicio (ISO8601 o string)
- `end_time`: Tiempo fin
- `where_conditions`: Dict con condiciones
- `limit`: Límite de resultados
- `convert_to_local_tz`: Convertir a timezone local

```python
df = influx.query_to_dataframe(
    measurement='temperatura',
    fields=['value', 'humidity'],
    start_time='2024-01-01T00:00:00Z',
    end_time='2024-01-31T23:59:59Z',
    limit=1000
)
```

### `read_last_n_points(measurement, n=100, fields=None, database=None)` ⭐ **NUEVO**
Lee los últimos N puntos.

```python
df = influx.read_last_n_points('temperatura', n=50)
```

### `read_time_range(measurement, start_time, end_time, fields=None, database=None)` ⭐ **NUEVO**
Lee datos en un rango de tiempo.

```python
df = influx.read_time_range(
    measurement='temperatura',
    start_time=datetime.now() - timedelta(hours=24),
    end_time=datetime.now()
)
```

### `get_data(query, database=None)`
Ejecuta una query InfluxQL y retorna DataFrame.

```python
df = influx.get_data("SELECT * FROM temperatura LIMIT 100")
```

### `query_builder(measurement, fields=None, where_conditions=None, **kwargs)`
Constructor de queries InfluxQL.

### `execute_query_builder(measurement, as_dataframe=True, **kwargs)`
Construye y ejecuta una query.

---

## 💾 GESTIÓN DE BASES DE DATOS

### `list_databases()` / `get_databases()`
Lista todas las bases de datos.

```python
databases = influx.list_databases()
# ['_internal', 'mi_db', 'test_db']
```

### `database_exists(database)`
Verifica si existe una base de datos.

### `create_database(database)`
Crea una nueva base de datos.

### `drop_database(database, confirm=True)`
Elimina una base de datos (requiere confirm=True).

### `get_database_info(database=None)`
Información completa de la base de datos.

```python
info = influx.get_database_info('mi_db')
# {'name': 'mi_db', 'measurements': [...], 'retention_policies': [...]}
```

---

## 📏 GESTIÓN DE MEASUREMENTS

### `list_measurements(database=None)` / `get_measurements(database=None)`
Lista todos los measurements.

```python
measurements = influx.list_measurements('mi_db')
# ['temperatura', 'humedad', 'presion']
```

### `measurement_exists(measurement, database=None)`
Verifica si existe un measurement.

### `drop_measurement(measurement, database=None, confirm=True)`
Elimina un measurement.

### `get_measurement_info(measurement, database=None)`
Información completa del measurement.

```python
info = influx.get_measurement_info('temperatura', 'mi_db')
# {
#   'name': 'temperatura',
#   'tags': ['sensor_id', 'location'],
#   'fields': {'value': 'float', 'status': 'string'},
#   'cardinality': 10,
#   'point_count': 5000
# }
```

### `get_measurement_cardinality(measurement, database=None)`
Número de series únicas (combinaciones de tags).

### `count_points(measurement, database=None, start_time=None, end_time=None)`
Cuenta puntos en un measurement.

---

## 🏷️ TAGS Y FIELDS

### `list_tags(measurement, database=None)`
Lista todos los tags de un measurement.

```python
tags = influx.list_tags('temperatura')
# ['sensor_id', 'location', 'type']
```

### `list_tag_values(measurement, tag_key, database=None)`
Lista valores de un tag específico.

```python
values = influx.list_tag_values('temperatura', 'location')
# ['oficina', 'almacen', 'sala']
```

### `list_fields(measurement, database=None)`
Lista campos con sus tipos.

```python
fields = influx.list_fields('temperatura')
# {'temperature': 'float', 'humidity': 'float', 'active': 'boolean'}
```

### `get_field_keys_grouped_by_type(measurement)`
Agrupa fields por tipo de dato.

### `build_query_fields(fields, operation)`
Construye parte de query aplicando operación a campos.

---

## 🔧 OPERACIONES AVANZADAS

### `delete(measurement, start_time=None, end_time=None, filters=None, database=None)`
Elimina datos de un measurement.

```python
influx.delete(
    measurement='temperatura',
    start_time='2024-01-01T00:00:00Z',
    end_time='2024-01-31T23:59:59Z'
)
```

### `downsample_data(measurement, target_measurement, aggregation_window, **kwargs)`
Crea versión downsampled de los datos.

```python
points = influx.downsample_data(
    measurement='raw_data',
    target_measurement='hourly_avg',
    aggregation_window='1h',
    aggregation_func='MEAN'
)
```

### `backup_measurement(measurement, output_file, start_time=None, end_time=None, database=None)`
Exporta measurement a CSV.

### `restore_measurement(measurement, input_file, tags=None, batch_size=5000, database=None)`
Restaura measurement desde CSV.

---

## 🔄 CONTINUOUS QUERIES

### `create_continuous_query(cq_name, measurement, target_measurement, aggregation_window, **kwargs)`
Crea una continuous query.

```python
influx.create_continuous_query(
    cq_name='hourly_avg',
    measurement='raw_data',
    target_measurement='hourly_data',
    aggregation_window='1h',
    aggregation_func='MEAN'
)
```

### `list_continuous_queries(database=None)`
Lista continuous queries.

### `drop_continuous_query(cq_name, database=None)`
Elimina una continuous query.

---

## ⏰ RETENTION POLICIES

### `get_retention_policies(database=None)`
Lista políticas de retención.

```python
policies = influx.get_retention_policies('mi_db')
# [{'name': 'autogen', 'duration': '0s', 'replicaN': 1, 'default': True}]
```

---

## 📊 MÉTRICAS Y CALIDAD

### `get_metrics()`
Obtiene métricas de rendimiento.

```python
metrics = influx.get_metrics()
# {
#   'total_writes': 100,
#   'total_points': 10000,
#   'failed_writes': 2,
#   'total_write_time': 5.2,
#   'avg_write_time': 0.052,
#   'success_rate': 98.0
# }
```

### `reset_metrics()`
Reinicia métricas.

### `calculate_data_quality_metrics(measurement, fields=None, **kwargs)`
Calcula métricas de calidad de datos.

```python
metrics = influx.calculate_data_quality_metrics('temperatura')
# {
#   'temperature': {
#     'count': 1000,
#     'missing': 10,
#     'missing_percentage': 1.0,
#     'mean': 25.5,
#     'std': 2.3,
#     'min': 18.0,
#     'max': 32.0,
#     'zeros': 0,
#     'outliers': 5
#   }
# }
```

---

## 🛠️ UTILIDADES

### `normalize_value_to_write(value)`
Normaliza un valor para escritura (limpia NaN, infinitos, None).

### `transaction(database=None)`
Context manager para operaciones transaccionales.

```python
with influx.transaction('mi_db'):
    influx.write_dataframe(measurement='datos', df=df1)
    influx.write_dataframe(measurement='datos', df=df2)
```

---

## 🆕 MÉTODOS NUEVOS EN ESTA VERSIÓN

- ⭐ `query_to_dataframe()` - Lectura simplificada con filtros
- ⭐ `read_last_n_points()` - Leer últimos N puntos
- ⭐ `read_time_range()` - Leer rango de tiempo
- ⭐ `convert_index_to_utc` - Parámetro en write_dataframe()
- ⭐ `get_measurements()` - Alias de compatibilidad
- ⭐ `get_databases()` - Alias de compatibilidad

---

## 📚 Ver También

- [Guía de Uso](INFLUXDB_USAGE.md) - Tutorial completo con ejemplos
- [Ejemplo Simple](../examples/influxdb_simple_example.py) - Código de ejemplo básico
- [Test con Datos Reales](../test_influxdb_real.py) - Test completo de integración
