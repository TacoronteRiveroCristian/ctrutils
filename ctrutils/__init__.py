"""
ctrutils - Librería minimalista de utilidades en Python.

Este paquete proporciona tres módulos principales para operaciones comunes
en proyectos de ciencia de datos e ingeniería de software.

Módulos:
    database.influxdb: Operaciones avanzadas con InfluxDB incluyendo validación
                      automática de datos, escritura paralela, downsampling,
                      backup/restore y métricas de calidad de datos.
    scheduler: Sistema de programación de tareas robusto tipo Airflow con
              dependencias entre tareas (DAGs), reintentos automáticos con
              backoff exponencial, callbacks y métricas de rendimiento.
    handler: Sistema unificado de logging y notificaciones con soporte para
            múltiples handlers (consola, archivos rotativos, Loki, Telegram).

Classes:
    InfluxdbOperation: Cliente avanzado para operaciones con InfluxDB.
    Scheduler: Gestor de tareas programadas con características production-ready.
    LoggingHandler: Gestor de configuración de logging con múltiples handlers.
    LokiHandler: Handler para enviar logs a Grafana Loki.
    TelegramBotHandler: Handler para enviar notificaciones a Telegram.

Examples:
    Uso básico de los componentes principales:

    >>> from ctrutils import InfluxdbOperation, Scheduler, LoggingHandler
    >>>
    >>> # InfluxDB - Cliente con validación automática
    >>> influx = InfluxdbOperation(host='localhost', port=8086)
    >>> influx.write_dataframe('medicion', df, validate_data=True)
    >>>
    >>> # Scheduler - Programación robusta de tareas
    >>> scheduler = Scheduler()
    >>> scheduler.add_job(func=mi_tarea, trigger='cron',
    ...                   job_id='tarea_diaria',
    ...                   trigger_args={'hour': '2', 'minute': '0'})
    >>> scheduler.start(blocking=True)
    >>>
    >>> # Logging - Configuración centralizada
    >>> logger = LoggingHandler(logger_name='mi_app')
    >>> logger.add_handlers([logger.create_stream_handler()])

Version:
    11.0.0

Author:
    Cristian Tacoronte Rivero

License:
    MIT

See Also:
    - Documentación: https://github.com/TacoronteRiveroCristian/ctrutils
    - PyPI: https://pypi.org/project/ctrutils/
"""

from .database.influxdb import InfluxdbOperation
from .scheduler import Scheduler
from .handler import LoggingHandler, LokiHandler, TelegramBotHandler

__all__ = [
    "InfluxdbOperation",
    "Scheduler",
    "LoggingHandler",
    "LokiHandler",
    "TelegramBotHandler",
]
