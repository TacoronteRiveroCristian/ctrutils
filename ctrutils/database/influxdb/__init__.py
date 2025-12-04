"""
Cliente avanzado para InfluxDB con características production-ready.

Este módulo proporciona la clase InfluxdbOperation con funcionalidades extendidas
para trabajar con InfluxDB, incluyendo validación automática de datos, escritura
paralela, downsampling, backup/restore y métricas de calidad.

Classes:
    InfluxdbOperation: Cliente principal con todas las operaciones de InfluxDB.

Features:
    - Validación automática de DataFrames (detección de NaN, infinitos, tipos)
    - Escritura paralela para grandes volúmenes de datos
    - Conversión automática de zonas horarias (UTC)
    - Downsampling y continuous queries
    - Backup y restore de measurements
    - Métricas de calidad de datos
    - Query builder para consultas complejas
    - Transacciones con rollback automático
    - Logging integrado y métricas de rendimiento

Examples:
    >>> from ctrutils.database.influxdb import InfluxdbOperation
    >>> import pandas as pd
    >>>
    >>> # Conexión y escritura básica
    >>> influx = InfluxdbOperation(host='localhost', port=8086,
    ...                            username='admin', password='password')
    >>> df = pd.DataFrame({'value': [1.0, 2.0, 3.0]})
    >>> influx.write_dataframe('medicion', df, database='mi_db',
    ...                        validate_data=True)
    >>>
    >>> # Consulta con DataFrame
    >>> result = influx.query('SELECT * FROM medicion LIMIT 10',
    ...                       database='mi_db', return_dataframe=True)

See Also:
    - Documentación: docs/INFLUXDB_USAGE.md
    - API Reference: docs/INFLUXDB_API_REFERENCE.md
    - Ejemplos: docs/INFLUXDB_EXAMPLES.md
"""

from .InfluxdbOperation import InfluxdbOperation

__all__ = ["InfluxdbOperation"]