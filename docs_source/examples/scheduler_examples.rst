============================
Ejemplos de Scheduler
============================

Scheduler Básico con Cron
==========================

Ejecutar tarea cada 5 minutos::

   from ctrutils.scheduler import Scheduler

   def enviar_reporte():
       print("Enviando reporte...")

   scheduler = Scheduler()
   scheduler.add_job(
       func=enviar_reporte,
       trigger='cron',
       job_id='reporte_cada_5min',
       trigger_args={'minute': '*/5'}
   )

   scheduler.start(blocking=True)

Pipeline ETL con Dependencias
==============================

Tareas secuenciales (extract -> transform -> load)::

   from ctrutils.scheduler import Scheduler, Task

   def extract_data():
       print("Extrayendo datos...")
       return {"status": "ok"}

   def transform_data():
       print("Transformando datos...")
       return {"status": "ok"}

   def load_data():
       print("Cargando datos...")

   scheduler = Scheduler()

   extract = Task(
       task_id='extract',
       func=extract_data,
       trigger_type='cron',
       trigger_args={'minute': '0', 'hour': '2'},
       max_retries=3
   )

   transform = Task(
       task_id='transform',
       func=transform_data,
       trigger_type='cron',
       trigger_args={'minute': '0', 'hour': '2'},
       dependencies=['extract']
   )

   load = Task(
       task_id='load',
       func=load_data,
       trigger_type='cron',
       trigger_args={'minute': '0', 'hour': '2'},
       dependencies=['transform']
   )

   scheduler.add_task(extract)
   scheduler.add_task(transform)
   scheduler.add_task(load)

   scheduler.start(blocking=True)

Tarea con Callbacks
====================

Ejecutar callbacks en caso de éxito o fallo::

   from ctrutils.scheduler import Scheduler

   def tarea_critica():
       # Simular tarea que puede fallar
       import random
       if random.random() > 0.5:
           raise Exception("Error simulado")
       return "Éxito"

   def on_success(result):
       print(f"Tarea exitosa: {result}")

   def on_failure(error):
       print(f"Tarea falló: {error}")
       # Enviar alerta

   def on_retry(error, attempt):
       print(f"Reintentando (intento {attempt}): {error}")

   scheduler = Scheduler()
   scheduler.add_job(
       func=tarea_critica,
       trigger='cron',
       job_id='backup',
       trigger_args={'hour': '3', 'minute': '0'},
       max_retries=5,
       retry_delay=300,  # 5 minutos
       on_success=on_success,
       on_failure=on_failure,
       on_retry=on_retry
   )

   scheduler.start(blocking=True)

Ejecución Condicional
======================

Ejecutar tarea solo si se cumple una condición::

   from ctrutils.scheduler import Scheduler, Task

   def es_dia_laboral():
       import datetime
       return datetime.datetime.now().weekday() < 5  # Lunes a Viernes

   def tarea_laboral():
       print("Ejecutando tarea de día laboral")

   task = Task(
       task_id='tarea_laboral',
       func=tarea_laboral,
       trigger_type='cron',
       trigger_args={'minute': '0', 'hour': '9'},
       condition=es_dia_laboral  # Solo ejecuta si retorna True
   )

   scheduler = Scheduler()
   scheduler.add_task(task)
   scheduler.start(blocking=True)

Monitoreo de Métricas
======================

Obtener métricas de ejecución::

   from ctrutils.scheduler import Scheduler

   scheduler = Scheduler()

   # ... agregar tareas ...

   scheduler.start()

   # En otro hilo o proceso, obtener métricas
   metrics = scheduler.get_all_metrics()
   print(f"Uptime: {metrics['global']['uptime_seconds']}s")
   print(f"Total jobs ejecutados: {metrics['global']['total_jobs_executed']}")
   print(f"Total fallos: {metrics['global']['total_failures']}")

   # Métricas por tarea
   for task_id, task_metrics in metrics['tasks'].items():
       print(f"\n{task_id}:")
       print(f"  Success rate: {task_metrics['success_rate']:.2%}")
       print(f"  Avg duration: {task_metrics['avg_duration']:.2f}s")

Referencia de API
=================

Para documentación completa, consulta :doc:`../api/scheduler`.
