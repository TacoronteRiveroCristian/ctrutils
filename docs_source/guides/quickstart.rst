===============
Guía de Inicio
===============

Instalación
===========

Instalación básica::

   pip install ctrutils

Instalación con Poetry::

   poetry add ctrutils

Verificar la instalación::

   python -c "import ctrutils; print(ctrutils.__version__)"

Scheduler Básico
================

Crear un scheduler básico::

   from ctrutils.scheduler import Scheduler

   def mi_tarea():
       print("Ejecutando tarea...")

   scheduler = Scheduler(timezone="Europe/Madrid")
   scheduler.add_job(
       func=mi_tarea,
       trigger="cron",
       job_id="tarea_cada_5min",
       trigger_args={"minute": "*/5"},
   )

   # Iniciar (nunca termina)
   scheduler.start(blocking=True)

Pipeline ETL con Dependencias
==============================

Crear un pipeline con dependencias entre tareas::

   from ctrutils.scheduler import Scheduler, Task

   scheduler = Scheduler()

   extract = Task(
       task_id="extract",
       func=extract_data,
       trigger_type="cron",
       trigger_args={"minute": "*/15"},
       max_retries=3,
   )

   transform = Task(
       task_id="transform",
       func=transform_data,
       trigger_type="cron",
       trigger_args={"minute": "*/15"},
       dependencies=["extract"],  # Solo ejecuta si extract OK
   )

   scheduler.add_task(extract)
   scheduler.add_task(transform)
   scheduler.start(blocking=True)

InfluxDB Básico
===============

Conexión y escritura básica::

   from ctrutils import InfluxdbOperation
   import pandas as pd

   influx = InfluxdbOperation(
       host='localhost',
       port=8086,
       username='admin',
       password='password'
   )

   df = pd.DataFrame({
       'value': [1.0, 2.0, 3.0],
       'sensor': ['A', 'B', 'C']
   })

   stats = influx.write_dataframe(
       measurement='mediciones',
       data=df,
       database='mi_db',
       validate_data=True,  # Limpia NaN automáticamente
   )

   print(f"Escritos: {stats['successful_points']} puntos")

Consultar Datos
===============

Consultar datos con DataFrame::

   result = influx.query(
       query='SELECT * FROM mediciones LIMIT 10',
       database='mi_db',
       return_dataframe=True
   )

   print(result.head())

Logging Básico
==============

Configurar logger con múltiples handlers::

   from ctrutils.handler import LoggingHandler
   import logging

   logger = LoggingHandler(
       logger_name="mi_app",
       level=logging.INFO,
   )

   logger.add_handlers([
       logger.create_stream_handler(),
       logger.create_rotating_file_handler(
           filename="app.log",
           max_bytes=10*1024*1024,  # 10MB
           backup_count=5,
       )
   ])

   logger.info("Aplicación iniciada")

Próximos Pasos
==============

- Ver :doc:`../api/index` para referencia completa de la API
- Ver :doc:`../examples/influxdb_examples` para ejemplos de InfluxDB
- Ver :doc:`../examples/scheduler_examples` para ejemplos de Scheduler
