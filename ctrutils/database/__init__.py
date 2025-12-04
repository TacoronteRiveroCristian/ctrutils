"""
Módulo de operaciones con bases de datos.

Este paquete proporciona clientes y utilidades para interactuar con diferentes
sistemas de bases de datos, con énfasis en bases de datos de series temporales.

Submódulos:
    influxdb: Cliente avanzado para InfluxDB con características production-ready.

Classes:
    InfluxdbOperation: Cliente completo para operaciones con InfluxDB.

Examples:
    >>> from ctrutils.database import InfluxdbOperation
    >>> influx = InfluxdbOperation(host='localhost', port=8086)
"""

from .influxdb import InfluxdbOperation

__all__ = ["InfluxdbOperation"]
