"""
Este módulo proporciona una clase Scheduler para gestionar tareas programadas
utilizando APScheduler, con integración con el sistema de logging de ctrutils.

Características principales:
- Ejecución continua tipo daemon (nunca termina)
- Soporte para dependencias y tareas secuenciales/condicionales
- Reintentos automáticos con backoff exponencial
- Callbacks y hooks (on_success, on_failure, on_retry)
- Monitoreo de estado y métricas
- Gestión robusta de errores y recursos
- Soporte completo para expresiones crontab
"""

import logging
import signal
import sys
import time
import threading
from collections import defaultdict
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Union

from apscheduler.events import (
    EVENT_JOB_ERROR,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_MISSED,
    EVENT_JOB_SUBMITTED,
    JobExecutionEvent,
)
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

try:
    from ctrutils.handler.logging.logging_handler import LoggingHandler
    HAS_LOGGING_HANDLER = True
except ImportError:
    HAS_LOGGING_HANDLER = False


class JobState(Enum):
    """
    Estados posibles de un job durante su ciclo de vida.

    Los estados representan las diferentes fases por las que pasa una tarea
    desde su creación hasta su finalización o fallo.

    Attributes:
        PENDING: La tarea está programada pero aún no ha comenzado su ejecución.
        RUNNING: La tarea está actualmente en ejecución.
        SUCCESS: La tarea se completó exitosamente sin errores.
        FAILED: La tarea falló después de agotar todos los reintentos.
        RETRYING: La tarea falló pero se reintentará automáticamente.
        SKIPPED: La tarea se omitió porque no cumplió su condición de ejecución
                o porque una dependencia falló.

    Examples:
        >>> if task.state == JobState.SUCCESS:
        ...     print("Tarea completada")
        >>> elif task.state == JobState.RETRYING:
        ...     print(f"Reintentando...")
    """
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


class JobMetrics:
    """
    Métricas de ejecución y monitoreo de un job.

    Esta clase mantiene estadísticas detalladas sobre las ejecuciones de una tarea,
    incluyendo contadores de éxitos/fallos, tiempos de ejecución, y tasa de éxito.

    Las métricas se actualizan automáticamente en cada ejecución y se pueden
    exportar a diccionario para logging o visualización.

    Attributes:
        total_runs (int): Número total de ejecuciones (incluye éxitos, fallos y reintentos).
        successes (int): Número de ejecuciones exitosas.
        failures (int): Número de ejecuciones fallidas (después de agotar reintentos).
        retries (int): Número total de intentos de reintento realizados.
        last_run_time (Optional[datetime]): Timestamp de la última ejecución.
        last_duration (Optional[float]): Duración en segundos de la última ejecución.
        last_state (Optional[JobState]): Estado final de la última ejecución.
        avg_duration (float): Duración promedio de las ejecuciones exitosas en segundos.

    Examples:
        >>> metrics = JobMetrics()
        >>> metrics.record_run(duration=1.5, state=JobState.SUCCESS)
        >>> print(f"Tasa de éxito: {metrics.to_dict()['success_rate']:.2%}")
        Tasa de éxito: 100.00%
    """

    def __init__(self):
        """
        Inicializa todas las métricas en cero.

        Las métricas comienzan vacías y se actualizan mediante el método
        record_run() después de cada ejecución de la tarea.
        """
        self.total_runs = 0
        self.successes = 0
        self.failures = 0
        self.retries = 0
        self.last_run_time: Optional[datetime] = None
        self.last_duration: Optional[float] = None
        self.last_state: Optional[JobState] = None
        self.avg_duration: float = 0.0
        self._durations: List[float] = []

    def record_run(self, duration: float, state: JobState):
        """
        Registra los resultados de una ejecución del job.

        Actualiza todos los contadores y métricas según el estado de la ejecución.
        Para ejecuciones exitosas, también actualiza el promedio de duración.

        Args:
            duration: Tiempo de ejecución en segundos (debe ser >= 0).
            state: Estado final de la ejecución (SUCCESS, FAILED, RETRYING).

        Examples:
            >>> metrics = JobMetrics()
            >>> metrics.record_run(1.5, JobState.SUCCESS)
            >>> metrics.record_run(2.1, JobState.SUCCESS)
            >>> assert metrics.avg_duration == 1.8  # (1.5 + 2.1) / 2
        """
        self.total_runs += 1
        self.last_run_time = datetime.now()
        self.last_duration = duration
        self.last_state = state

        if state == JobState.SUCCESS:
            self.successes += 1
            self._durations.append(duration)
            self.avg_duration = sum(self._durations) / len(self._durations)
        elif state == JobState.FAILED:
            self.failures += 1
        elif state == JobState.RETRYING:
            self.retries += 1

    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte las métricas a un diccionario serializable.

        Returns:
            Dict con las siguientes claves:
                - total_runs (int): Total de ejecuciones
                - successes (int): Ejecuciones exitosas
                - failures (int): Ejecuciones fallidas
                - retries (int): Total de reintentos
                - success_rate (float): Porcentaje de éxito (0.0 a 1.0)
                - last_run_time (str|None): ISO timestamp de última ejecución
                - last_duration (float|None): Duración de última ejecución
                - last_state (str|None): Estado de última ejecución
                - avg_duration (float): Duración promedio de ejecuciones exitosas

        Examples:
            >>> metrics = JobMetrics()
            >>> metrics.record_run(1.5, JobState.SUCCESS)
            >>> data = metrics.to_dict()
            >>> print(data['success_rate'])  # 1.0
            1.0
        """
        return {
            "total_runs": self.total_runs,
            "successes": self.successes,
            "failures": self.failures,
            "retries": self.retries,
            "success_rate": self.successes / self.total_runs if self.total_runs > 0 else 0.0,
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "last_duration": self.last_duration,
            "last_state": self.last_state.value if self.last_state else None,
            "avg_duration": self.avg_duration,
        }


class Task:
    """
    Representa una tarea programable con dependencias y reintentos.
    """

    def __init__(
        self,
        task_id: str,
        func: Callable,
        trigger_type: str,
        trigger_args: Dict[str, Any],
        max_retries: int = 3,
        retry_delay: int = 60,
        retry_backoff: float = 2.0,
        timeout: Optional[int] = None,
        dependencies: Optional[List[str]] = None,
        on_success: Optional[Callable] = None,
        on_failure: Optional[Callable] = None,
        on_retry: Optional[Callable] = None,
        condition: Optional[Callable[[], bool]] = None,
        args: Optional[tuple] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ):
        """
        Inicializa una tarea.

        :param task_id: Identificador único de la tarea.
        :param func: Función a ejecutar.
        :param trigger_type: Tipo de trigger ('cron', 'interval', 'date').
        :param trigger_args: Argumentos para el trigger.
        :param max_retries: Número máximo de reintentos en caso de fallo.
        :param retry_delay: Delay inicial entre reintentos (segundos).
        :param retry_backoff: Multiplicador para el delay de reintento (backoff exponencial).
        :param timeout: Timeout de ejecución en segundos.
        :param dependencies: Lista de task_ids que deben completarse antes.
        :param on_success: Callback a ejecutar en caso de éxito.
        :param on_failure: Callback a ejecutar en caso de fallo.
        :param on_retry: Callback a ejecutar en cada reintento.
        :param condition: Función que retorna True/False para ejecutar condicionalmente.
        :param args: Argumentos posicionales para la función.
        :param kwargs: Argumentos nombrados para la función.
        """
        self.task_id = task_id
        self.func = func
        self.trigger_type = trigger_type
        self.trigger_args = trigger_args
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_backoff = retry_backoff
        self.timeout = timeout
        self.dependencies = dependencies or []
        self.on_success = on_success
        self.on_failure = on_failure
        self.on_retry = on_retry
        self.condition = condition
        self.args = args or ()
        self.kwargs = kwargs or {}

        self.current_retry = 0
        self.state = JobState.PENDING
        self.metrics = JobMetrics()


class Scheduler:
    """
    Scheduler robusto y eficiente para gestión de tareas programadas.

    Características:
    - Ejecución continua sin terminar
    - Dependencias entre tareas
    - Reintentos automáticos
    - Callbacks y hooks
    - Monitoreo de estado
    - Gestión de señales para shutdown graceful
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        timezone: str = "UTC",
        max_workers: int = 10,
        coalesce: bool = True,
        misfire_grace_time: int = 300,
        **scheduler_options: Any,
    ):
        """
        Inicializa el Scheduler.

        :param logger: Instancia de logger a utilizar.
        :param timezone: Zona horaria para el scheduler.
        :param max_workers: Número máximo de workers concurrentes.
        :param coalesce: Si True, combina múltiples ejecuciones pendientes en una.
        :param misfire_grace_time: Tiempo de gracia para ejecuciones perdidas (segundos).
        :param scheduler_options: Opciones adicionales para APScheduler.
        """
        # Logger setup
        if logger:
            self.logger = logger
        elif HAS_LOGGING_HANDLER:
            log_handler = LoggingHandler(
                level=logging.INFO,
                logger_name="ctrutils.scheduler",
                message_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            self.logger = log_handler.add_handlers([log_handler.create_stream_handler()])
        else:
            self.logger = logging.getLogger("ctrutils.scheduler")
            self.logger.setLevel(logging.INFO)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(
                    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
                )
                self.logger.addHandler(handler)

        # Scheduler configuration
        job_defaults = {
            "coalesce": coalesce,
            "max_instances": 1,
            "misfire_grace_time": misfire_grace_time,
        }

        self.scheduler = BackgroundScheduler(
            timezone=timezone,
            job_defaults=job_defaults,
            executors={"default": {"type": "threadpool", "max_workers": max_workers}},
            **scheduler_options,
        )

        # Task management
        self.tasks: Dict[str, Task] = {}
        self.task_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.completed_tasks: Set[str] = set()
        self._lock = threading.RLock()
        self._running = False
        self._shutdown_event = threading.Event()

        # Metrics
        self.global_metrics = {
            "total_jobs_executed": 0,
            "total_failures": 0,
            "total_retries": 0,
            "start_time": None,
        }

        # Setup event listeners
        self._add_event_listeners()

        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """
        Configura manejadores para señales del sistema (SIGINT, SIGTERM).

        Permite un graceful shutdown cuando el scheduler recibe señales de terminación,
        completando las tareas en ejecución antes de cerrar.

        Internal:
            Este método es privado y se llama automáticamente durante __init__().
            No debe ser invocado directamente por usuarios de la librería.

        Signals:
            - SIGINT (Ctrl+C): Inicia shutdown graceful y termina el programa.
            - SIGTERM: Inicia shutdown graceful desde el sistema operativo.

        Thread Safety:
            Thread-safe, utiliza RLock interno para sincronización.
        """
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
            self.shutdown(wait=True)
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _add_event_listeners(self):
        """
        Añade listeners para los eventos del scheduler.

        Configura callbacks para los eventos de APScheduler (ejecución, error, missed, submit)
        y actualiza las métricas globales y logs según el tipo de evento.

        Internal:
            Este método es privado y se llama automáticamente durante __init__().

        Events:
            - EVENT_JOB_EXECUTED: Job completado exitosamente, incrementa contador.
            - EVENT_JOB_ERROR: Job falló, incrementa failures y registra error con traceback.
            - EVENT_JOB_MISSED: Job perdió su ventana de ejecución por misfire.
            - EVENT_JOB_SUBMITTED: Job enviado al executor para procesamiento.
        """
        def job_listener(event: JobExecutionEvent):
            if event.code == EVENT_JOB_ERROR:
                self.global_metrics["total_failures"] += 1
                self.logger.error(
                    f"Job '{event.job_id}' failed: {event.exception}",
                    exc_info=event.exception,
                )
            elif event.code == EVENT_JOB_EXECUTED:
                self.global_metrics["total_jobs_executed"] += 1
                self.logger.info(f"Job '{event.job_id}' executed successfully.")
            elif event.code == EVENT_JOB_MISSED:
                self.logger.warning(f"Job '{event.job_id}' missed its execution window.")
            elif event.code == EVENT_JOB_SUBMITTED:
                self.logger.debug(f"Job '{event.job_id}' submitted to executor.")

        self.scheduler.add_listener(
            job_listener,
            mask=EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED | EVENT_JOB_SUBMITTED,
        )

    def _wrap_task_execution(self, task: Task) -> Callable:
        """
        Envuelve la ejecución de una tarea con lógica de reintentos, dependencias y callbacks.

        Crea un wrapper que implementa la lógica completa de ejecución de tareas:
        verificación de condiciones, validación de dependencias, manejo de reintentos
        con backoff exponencial, timeouts, callbacks y actualización de métricas.

        Args:
            task: Instancia de Task a envolver con la lógica de ejecución.

        Returns:
            Callable: Función wrapper que ejecuta la tarea con toda la lógica adicional.

        Internal:
            Este método es privado y se llama automáticamente desde add_task().
            El wrapper resultante es el que realmente se registra en APScheduler.

        Behavior:
            1. Verifica condición de ejecución (condition callable)
            2. Valida que todas las dependencias estén completadas
            3. Ejecuta la función con timeout si está especificado
            4. Implementa reintentos automáticos con backoff exponencial
            5. Ejecuta callbacks (on_success, on_failure, on_retry)
            6. Actualiza métricas y estado de la tarea
        """
        @wraps(task.func)
        def wrapper():
            # Check condition
            if task.condition and not task.condition():
                self.logger.info(f"Task '{task.task_id}' skipped due to condition.")
                task.state = JobState.SKIPPED
                return

            # Check dependencies
            with self._lock:
                for dep_id in task.dependencies:
                    if dep_id not in self.completed_tasks:
                        self.logger.warning(
                            f"Task '{task.task_id}' skipped. Dependency '{dep_id}' not completed."
                        )
                        task.state = JobState.SKIPPED
                        return

            # Execute with retries
            start_time = time.time()
            task.state = JobState.RUNNING

            for attempt in range(task.max_retries + 1):
                try:
                    # Execute with timeout if specified
                    if task.timeout:
                        result = self._execute_with_timeout(
                            task.func, task.args, task.kwargs, task.timeout
                        )
                    else:
                        result = task.func(*task.args, **task.kwargs)

                    # Success
                    duration = time.time() - start_time
                    task.state = JobState.SUCCESS
                    task.metrics.record_run(duration, JobState.SUCCESS)

                    with self._lock:
                        self.completed_tasks.add(task.task_id)

                    if task.on_success:
                        try:
                            task.on_success(result)
                        except Exception as e:
                            self.logger.error(
                                f"on_success callback failed for '{task.task_id}': {e}"
                            )

                    self.logger.info(
                        f"Task '{task.task_id}' completed successfully in {duration:.2f}s"
                    )
                    return result

                except Exception as e:
                    task.current_retry = attempt

                    if attempt < task.max_retries:
                        # Retry
                        task.state = JobState.RETRYING
                        task.metrics.record_run(time.time() - start_time, JobState.RETRYING)
                        self.global_metrics["total_retries"] += 1

                        delay = task.retry_delay * (task.retry_backoff ** attempt)
                        self.logger.warning(
                            f"Task '{task.task_id}' failed (attempt {attempt + 1}/{task.max_retries + 1}). "
                            f"Retrying in {delay:.0f}s. Error: {e}"
                        )

                        if task.on_retry:
                            try:
                                task.on_retry(e, attempt + 1)
                            except Exception as retry_error:
                                self.logger.error(
                                    f"on_retry callback failed for '{task.task_id}': {retry_error}"
                                )

                        time.sleep(delay)
                    else:
                        # Final failure
                        duration = time.time() - start_time
                        task.state = JobState.FAILED
                        task.metrics.record_run(duration, JobState.FAILED)

                        self.logger.error(
                            f"Task '{task.task_id}' failed after {task.max_retries + 1} attempts. "
                            f"Error: {e}",
                            exc_info=True,
                        )

                        if task.on_failure:
                            try:
                                task.on_failure(e)
                            except Exception as failure_error:
                                self.logger.error(
                                    f"on_failure callback failed for '{task.task_id}': {failure_error}"
                                )

                        raise

        return wrapper

    def _execute_with_timeout(
        self, func: Callable, args: tuple, kwargs: Dict[str, Any], timeout: int
    ) -> Any:
        """
        Ejecuta una función con timeout usando threading.

        Crea un thread daemon para ejecutar la función y espera hasta el timeout
        especificado. Si el thread no termina a tiempo, lanza TimeoutError.

        Args:
            func: Función a ejecutar con timeout.
            args: Argumentos posicionales para la función.
            kwargs: Argumentos nombrados para la función.
            timeout: Tiempo máximo de ejecución en segundos.

        Returns:
            Any: El valor de retorno de la función ejecutada.

        Raises:
            TimeoutError: Si la ejecución excede el timeout especificado.
            Exception: Cualquier excepción lanzada por la función original.

        Internal:
            Este método es privado y se usa internamente por _wrap_task_execution()
            cuando una Task tiene timeout configurado.

        Note:
            Usa un thread daemon que se terminará cuando el programa principal termine,
            incluso si la función aún está ejecutándose.
        """
        result = [None]
        exception = [None]

        def target():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            raise TimeoutError(f"Task execution exceeded timeout of {timeout}s")

        if exception[0]:
            raise exception[0]

        return result[0]

    def add_task(self, task: Task) -> None:
        """
        Añade una nueva tarea al scheduler.

        :param task: Instancia de Task a añadir.
        """
        with self._lock:
            if task.task_id in self.tasks:
                raise ValueError(f"Task '{task.task_id}' already exists.")

            # Validate dependencies
            for dep_id in task.dependencies:
                if dep_id not in self.tasks and dep_id not in [t.task_id for t in self.tasks.values()]:
                    self.logger.warning(
                        f"Task '{task.task_id}' has dependency '{dep_id}' that doesn't exist yet."
                    )

            self.tasks[task.task_id] = task

            # Add task to scheduler
            triggers = {
                "cron": CronTrigger,
                "interval": IntervalTrigger,
                "date": DateTrigger,
            }
            trigger_class = triggers.get(task.trigger_type)
            if not trigger_class:
                raise ValueError(f"Trigger '{task.trigger_type}' not supported.")

            wrapped_func = self._wrap_task_execution(task)

            self.scheduler.add_job(
                wrapped_func,
                trigger=trigger_class(**task.trigger_args),
                id=task.task_id,
                name=task.task_id,
                replace_existing=True,
            )

            self.logger.info(
                f"Task '{task.task_id}' added with trigger '{task.trigger_type}'. "
                f"Dependencies: {task.dependencies or 'None'}"
            )

    def add_job(
        self,
        func: Callable,
        trigger: str,
        job_id: str,
        trigger_args: Dict[str, Any],
        max_retries: int = 3,
        retry_delay: int = 60,
        dependencies: Optional[List[str]] = None,
        on_success: Optional[Callable] = None,
        on_failure: Optional[Callable] = None,
        **job_kwargs: Any,
    ) -> None:
        """
        Añade un nuevo trabajo al scheduler (método simplificado).

        :param func: La función a ejecutar.
        :param trigger: Tipo de trigger ('cron', 'interval', 'date').
        :param job_id: ID único para el trabajo.
        :param trigger_args: Argumentos para el trigger.
        :param max_retries: Número máximo de reintentos.
        :param retry_delay: Delay entre reintentos (segundos).
        :param dependencies: Lista de job_ids que deben completarse antes.
        :param on_success: Callback en caso de éxito.
        :param on_failure: Callback en caso de fallo.
        :param job_kwargs: Argumentos adicionales (args, kwargs, etc.).
        """
        task = Task(
            task_id=job_id,
            func=func,
            trigger_type=trigger,
            trigger_args=trigger_args,
            max_retries=max_retries,
            retry_delay=retry_delay,
            dependencies=dependencies,
            on_success=on_success,
            on_failure=on_failure,
            args=job_kwargs.get("args", ()),
            kwargs=job_kwargs.get("kwargs", {}),
        )
        self.add_task(task)

    def remove_job(self, job_id: str) -> None:
        """
        Elimina un trabajo del scheduler.

        :param job_id: ID del trabajo a eliminar.
        """
        with self._lock:
            if job_id in self.tasks:
                del self.tasks[job_id]
                self.completed_tasks.discard(job_id)

        try:
            self.scheduler.remove_job(job_id)
            self.logger.info(f"Job '{job_id}' removed.")
        except Exception as e:
            self.logger.warning(f"Job '{job_id}' not found in scheduler: {e}")

    def get_jobs(self) -> List[Any]:
        """
        Obtiene la lista de trabajos programados.

        :return: Lista de jobs del scheduler.
        """
        return self.scheduler.get_jobs()

    def get_task_metrics(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene las métricas de una tarea específica.

        :param task_id: ID de la tarea.
        :return: Diccionario con las métricas o None.
        """
        task = self.tasks.get(task_id)
        if task:
            return task.metrics.to_dict()
        return None

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Obtiene todas las métricas del scheduler.

        :return: Diccionario con métricas globales y por tarea.
        """
        task_metrics = {
            task_id: task.metrics.to_dict()
            for task_id, task in self.tasks.items()
        }

        uptime = None
        if self.global_metrics["start_time"]:
            uptime = (datetime.now() - self.global_metrics["start_time"]).total_seconds()

        return {
            "global": {
                **self.global_metrics,
                "uptime_seconds": uptime,
                "is_running": self._running,
                "total_tasks": len(self.tasks),
                "completed_tasks": len(self.completed_tasks),
            },
            "tasks": task_metrics,
        }

    def start(self, blocking: bool = False) -> None:
        """
        Inicia el scheduler.

        :param blocking: Si True, mantiene el scheduler ejecutándose indefinidamente.
        """
        if not self.scheduler.running:
            self.scheduler.start()
            self._running = True
            self.global_metrics["start_time"] = datetime.now()
            self.logger.info("Scheduler started.")

            if blocking:
                self.logger.info("Scheduler running in blocking mode. Press Ctrl+C to stop.")
                try:
                    # Keep the main thread alive
                    while not self._shutdown_event.is_set():
                        time.sleep(1)
                except (KeyboardInterrupt, SystemExit):
                    self.logger.info("Shutdown signal received.")
                finally:
                    self.shutdown(wait=True)

    def shutdown(self, wait: bool = True) -> None:
        """
        Detiene el scheduler.

        :param wait: Si True, espera a que terminen los jobs en ejecución.
        """
        if self.scheduler.running:
            self._shutdown_event.set()
            self.scheduler.shutdown(wait=wait)
            self._running = False
            self.logger.info("Scheduler shut down.")

    def pause_job(self, job_id: str) -> None:
        """
        Pausa temporalmente la ejecución de una tarea programada.

        La tarea permanece registrada pero no se ejecutará según su schedule
        hasta que se llame a resume_job(). Las ejecuciones que ocurran mientras
        está pausada se considerarán "missed" según la política de misfire.

        Args:
            job_id: Identificador único de la tarea a pausar.

        Raises:
            JobLookupError: Si el job_id no existe en el scheduler.

        Examples:
            >>> scheduler.pause_job("tarea_nocturna")
            >>> # Durante el día, hacer mantenimiento...
            >>> scheduler.resume_job("tarea_nocturna")

        See Also:
            resume_job: Reactiva una tarea pausada.
            remove_job: Elimina permanentemente una tarea.
        """
        self.scheduler.pause_job(job_id)
        self.logger.info(f"Job '{job_id}' paused.")

    def resume_job(self, job_id: str) -> None:
        """
        Reanuda la ejecución de una tarea previamente pausada.

        La tarea volverá a ejecutarse según su schedule configurado. Si la siguiente
        ejecución ya pasó, se ejecutará inmediatamente o según la política de misfire.

        Args:
            job_id: Identificador único de la tarea a reanudar.

        Raises:
            JobLookupError: Si el job_id no existe en el scheduler.

        Examples:
            >>> scheduler.pause_job("backup_nocturno")
            >>> # Realizar mantenimiento...
            >>> scheduler.resume_job("backup_nocturno")

        See Also:
            pause_job: Pausa una tarea temporalmente.
        """
        self.scheduler.resume_job(job_id)
        self.logger.info(f"Job '{job_id}' resumed.")

    def reschedule_job(self, job_id: str, trigger_type: str, **trigger_args: Any) -> None:
        """
        Re-programa un job existente con un nuevo trigger.

        :param job_id: ID del job a re-programar.
        :param trigger_type: Nuevo tipo de trigger.
        :param trigger_args: Argumentos para el nuevo trigger.
        """
        triggers = {
            "cron": CronTrigger,
            "interval": IntervalTrigger,
            "date": DateTrigger,
        }
        trigger_class = triggers.get(trigger_type)
        if not trigger_class:
            raise ValueError(f"Trigger '{trigger_type}' not supported.")

        self.scheduler.reschedule_job(
            job_id,
            trigger=trigger_class(**trigger_args)
        )
        self.logger.info(f"Job '{job_id}' rescheduled with trigger '{trigger_type}'.")

    def is_running(self) -> bool:
        """
        Verifica si el scheduler está actualmente ejecutándose.

        Returns:
            bool: True si el scheduler está activo y procesando tareas,
                  False en caso contrario.

        Examples:
            >>> scheduler.start()
            >>> assert scheduler.is_running() is True
            >>> scheduler.shutdown()
            >>> assert scheduler.is_running() is False

        See Also:
            start: Inicia el scheduler.
            shutdown: Detiene el scheduler.
        """
        return self._running and self.scheduler.running

    def print_jobs(self) -> None:
        """
        Imprime información de todos los jobs programados en el scheduler.

        Muestra una tabla formateada con información de cada job incluyendo:
        ID, nombre, trigger, próxima ejecución y estado.

        Esta función es útil para debugging y monitoreo del estado del scheduler.

        Examples:
            >>> scheduler.add_job(func=tarea1, trigger='cron',
            ...                   job_id='tarea1',
            ...                   trigger_args={'minute': '*/5'})
            >>> scheduler.print_jobs()
            Jobstore default:
                tarea1 (trigger: cron[minute='*/5'], next run at: ...)

        See Also:
            get_jobs: Obtiene lista programática de jobs.
            get_all_metrics: Obtiene métricas de todos los jobs.
        """
        self.scheduler.print_jobs()
