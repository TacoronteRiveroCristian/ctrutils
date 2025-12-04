"""
Módulo de programación de tareas robusta tipo Airflow.

Este módulo proporciona un scheduler production-ready con características avanzadas
para la gestión de tareas programadas y pipelines de datos.

Características principales:
    - Ejecución continua daemon (nunca termina, ideal para servicios)
    - Dependencias entre tareas (DAGs) para pipelines ETL complejos
    - Reintentos automáticos con backoff exponencial configurable
    - Callbacks y hooks personalizables (on_success, on_failure, on_retry)
    - Ejecución condicional de tareas basada en predicados
    - Métricas detalladas de rendimiento y monitoreo
    - Timeouts por tarea para evitar bloqueos
    - Graceful shutdown que completa tareas en ejecución
    - Thread-safe para entornos concurrentes

Classes:
    Scheduler: Gestor principal de tareas programadas basado en APScheduler.
    Task: Representa una tarea con dependencias, reintentos y configuración avanzada.
    JobState: Enum de estados del ciclo de vida de un job (PENDING, RUNNING, etc.).
    JobMetrics: Clase de métricas de ejecución y monitoreo de tareas.

Examples:
    Scheduler básico con cron:

    >>> from ctrutils.scheduler import Scheduler
    >>>
    >>> scheduler = Scheduler()
    >>> scheduler.add_job(
    ...     func=mi_funcion,
    ...     trigger='cron',
    ...     job_id='tarea_cada_5min',
    ...     trigger_args={'minute': '*/5'}
    ... )
    >>> scheduler.start(blocking=True)  # Ejecuta indefinidamente

    Pipeline ETL con dependencias:

    >>> from ctrutils.scheduler import Scheduler, Task
    >>>
    >>> scheduler = Scheduler()
    >>>
    >>> # Definir tareas con dependencias
    >>> extract = Task(
    ...     task_id='extract',
    ...     func=extract_data,
    ...     trigger_type='cron',
    ...     trigger_args={'minute': '0', 'hour': '2'},
    ...     max_retries=3
    ... )
    >>>
    >>> transform = Task(
    ...     task_id='transform',
    ...     func=transform_data,
    ...     trigger_type='cron',
    ...     trigger_args={'minute': '0', 'hour': '2'},
    ...     dependencies=['extract']  # Solo ejecuta si extract OK
    ... )
    >>>
    >>> scheduler.add_task(extract)
    >>> scheduler.add_task(transform)
    >>> scheduler.start(blocking=True)

    Tarea con callbacks y reintentos:

    >>> def on_success(result):
    ...     print(f"Tarea exitosa: {result}")
    >>>
    >>> def on_failure(error):
    ...     print(f"Tarea falló: {error}")
    >>>
    >>> scheduler.add_job(
    ...     func=tarea_critica,
    ...     trigger='cron',
    ...     job_id='backup',
    ...     trigger_args={'hour': '3', 'minute': '0'},
    ...     max_retries=5,
    ...     retry_delay=300,  # 5 minutos
    ...     on_success=on_success,
    ...     on_failure=on_failure
    ... )

See Also:
    - Documentación completa: docs/scheduler/README.md
    - Cheat sheet: docs/scheduler/SCHEDULER_CHEATSHEET.md
    - API Reference: https://ctrutils.readthedocs.io/
"""

from .scheduler import Scheduler, Task, JobState, JobMetrics

__all__ = ["Scheduler", "Task", "JobState", "JobMetrics"]

