"""
Este módulo proporciona una clase Scheduler para gestionar tareas programadas
utilizando APScheduler, con integración con el sistema de logging de ctrutils.
"""

import logging
from typing import Any, Callable, Dict, Optional

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

try:
    from ctrutils.handler.logging.logging_handler import LoggingHandler
    HAS_LOGGING_HANDLER = True
except ImportError:
    HAS_LOGGING_HANDLER = False


class Scheduler:
    """
    Clase para gestionar tareas programadas con APScheduler y logging integrado.
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        timezone: str = "UTC",
        **scheduler_options: Any,
    ):
        """
        Inicializa el Scheduler.

        :param logger: Instancia de logger a utilizar. Si no se proporciona, se crea una nueva.
        :param timezone: Zona horaria para el scheduler.
        :param scheduler_options: Opciones adicionales para el BackgroundScheduler de APScheduler.
        """
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
            # Fallback a logging estándar si LoggingHandler no está disponible
            self.logger = logging.getLogger("ctrutils.scheduler")
            self.logger.setLevel(logging.INFO)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(
                    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
                )
                self.logger.addHandler(handler)

        self.scheduler = BackgroundScheduler(
            timezone=timezone, **scheduler_options
        )
        self._add_logging_listener()

    def _add_logging_listener(self):
        """Añade un listener para los eventos del scheduler."""
        def listener(event):
            if event.code == EVENT_JOB_ERROR:
                self.logger.error(
                    f"Job '{event.job_id}' crashed: {event.exception}",
                    exc_info=event.exception,
                )
            else:
                self.logger.info(f"Job '{event.job_id}' executed successfully.")

        self.scheduler.add_listener(
            listener,
            mask=EVENT_JOB_EXECUTED | EVENT_JOB_ERROR,
        )

    def add_job(
        self,
        func: Callable,
        trigger: str,
        job_id: str,
        trigger_args: Dict[str, Any],
        **job_kwargs: Any,
    ) -> None:
        """
        Añade un nuevo trabajo al scheduler.

        :param func: La función a ejecutar.
        :param trigger: Tipo de trigger ('cron', 'interval', 'date').
        :param job_id: ID único para el trabajo.
        :param trigger_args: Argumentos para el trigger.
        :param job_kwargs: Argumentos adicionales para el trabajo (ej. `args`, `kwargs`).
        """
        triggers = {
            "cron": CronTrigger,
            "interval": IntervalTrigger,
            "date": DateTrigger,
        }
        trigger_class = triggers.get(trigger)
        if not trigger_class:
            raise ValueError(f"Trigger '{trigger}' no soportado.")

        self.scheduler.add_job(
            func, trigger=trigger_class(**trigger_args), id=job_id, **job_kwargs
        )
        self.logger.info(f"Job '{job_id}' added with trigger '{trigger}'.")

    def remove_job(self, job_id: str) -> None:
        """
        Elimina un trabajo del scheduler.

        :param job_id: ID del trabajo a eliminar.
        """
        self.scheduler.remove_job(job_id)
        self.logger.info(f"Job '{job_id}' removed.")

    def get_jobs(self) -> list:
        """
        Obtiene la lista de trabajos programados.

        :return: Lista de jobs del scheduler.
        """
        return self.scheduler.get_jobs()

    def start(self) -> None:
        """Inicia el scheduler en segundo plano."""
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.info("Scheduler started.")

    def shutdown(self) -> None:
        """Detiene el scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("Scheduler shut down.")
