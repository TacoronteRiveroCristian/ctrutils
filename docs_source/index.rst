=================================
ctrutils - Documentación Oficial
=================================

.. image:: https://img.shields.io/badge/python-3.10%2B-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python Version

.. image:: https://img.shields.io/badge/license-MIT-green.svg
   :target: https://github.com/TacoronteRiveroCristian/ctrutils/blob/main/LICENSE
   :alt: License

**ctrutils** es una librería minimalista de utilidades en Python enfocada en:

- 🗄️ **InfluxDB**: Operaciones avanzadas con validación automática, escritura paralela, downsampling y backup
- ⏰ **Scheduler**: Programación robusta de tareas tipo Airflow con dependencias, reintentos y métricas
- 📝 **Handler**: Sistema de logging y notificaciones (consola, archivos, Loki, Telegram)

Versión actual: **11.0.0**

Inicio Rápido
=============

Instalación::

   pip install ctrutils

Ejemplo mínimo de Scheduler::

   from ctrutils.scheduler import Scheduler

   scheduler = Scheduler()
   scheduler.add_job(
       func=mi_funcion,
       trigger="cron",
       job_id="tarea_cada_5min",
       trigger_args={"minute": "*/5"},
   )
   scheduler.start(blocking=True)  # Nunca termina

Ejemplo de InfluxDB::

   from ctrutils import InfluxdbOperation
   import pandas as pd

   influx = InfluxdbOperation(host='localhost', port=8086)
   df = pd.DataFrame({'value': [1, 2, 3]})
   influx.write_dataframe('medicion', df, database='mi_db')

.. toctree::
   :maxdepth: 2
   :caption: Guías de Usuario

   guides/quickstart

.. toctree::
   :maxdepth: 2
   :caption: Referencia de API

   api/index
   api/influxdb
   api/scheduler
   api/handler

.. toctree::
   :maxdepth: 2
   :caption: Ejemplos

   examples/influxdb_examples
   examples/scheduler_examples

.. toctree::
   :maxdepth: 1
   :caption: Desarrollo

   changelog
   contributing

Índices y Tablas
================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Enlaces
=======

- **GitHub**: https://github.com/TacoronteRiveroCristian/ctrutils
- **PyPI**: https://pypi.org/project/ctrutils/
- **Issues**: https://github.com/TacoronteRiveroCristian/ctrutils/issues
