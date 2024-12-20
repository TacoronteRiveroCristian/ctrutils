"""
Este modulo proporciona una clase base, LoggingHandler, para la configuracion y manejo
de logs en aplicaciones Python. Permite registrar mensajes de log en consola o en un archivo,
y proporciona metodos para personalizar el formato del log y la configuracion del logger.
"""

import logging
from logging import FileHandler, StreamHandler
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional


class LoggingHandler:
    """
    Clase para configurar y manejar logs en aplicaciones Python.

    Esta clase permite registrar mensajes de log en consola o en un archivo.
    Incluye opciones para rotar los logs segun un periodo de retencion y configurar
    el formato de los mensajes.

    Ejemplo de uso:

    .. code-block:: python

        from logging_handler import LoggingHandler

        # Configurar un logger para consola
        handler = LoggingHandler()
        logger = handler.configure_logger()
        logger.info("Log en consola configurado correctamente")

        # Configurar un logger para archivo con rotacion diaria y 7 dias de retencion
        handler = LoggingHandler()
        logger = handler.configure_logger(
            log_file="app.log",
            log_retention_period="1d",
            log_backup_period=7
        )
        logger.info("Log en archivo configurado correctamente")
    """

    def __init__(self):
        """
        Inicializa una instancia de LoggingHandler con configuraciones basicas.
        """
        self._log_format: str = (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.logger: Optional[logging.Logger] = None

    @property
    def log_format(self) -> str:
        """
        Accede al formato de log actual.

        :return: El formato de log actual.
        :rtype: str
        """
        return self._log_format

    @log_format.setter
    def log_format(self, new_format: str) -> None:
        """
        Modifica el formato de log actual.

        :param new_format: El nuevo formato de log.
        :type new_format: str
        :raises ValueError: Si el nuevo formato de log esta vacio.
        """
        if not new_format:
            raise ValueError("El formato de log no puede estar vacio.")
        self._log_format = new_format

    def _create_log_directory(self, log_file: Path) -> None:
        """
        Crea la carpeta para el archivo de log si no existe.

        :param log_file: Ruta del archivo de log.
        :type log_file: Path
        """
        log_file.parent.mkdir(parents=True, exist_ok=True)

    def _create_timed_rotating_file_handler(
        self,
        log_file: Path,
        log_retention_period: str,
        log_backup_period: int,
    ) -> TimedRotatingFileHandler:
        """
        Crea un handler con rotacion basada en tiempo.

        :param log_file: Ruta del archivo de log.
        :type log_file: Path
        :param log_retention_period: Periodo de retencion en formato '<n>d', '<n>w', etc.
        :type log_retention_period: str
        :param log_backup_period: Numero de backups a mantener.
        :type log_backup_period: int
        :return: Handler configurado.
        :rtype: TimedRotatingFileHandler
        """
        self._create_log_directory(log_file)
        unit = log_retention_period[-1].upper()
        interval = int(log_retention_period[:-1])
        handler = TimedRotatingFileHandler(
            filename=str(log_file),
            when=unit,
            interval=interval,
            backupCount=log_backup_period,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(self.log_format))
        return handler

    def _create_file_handler(self, log_file: Path) -> FileHandler:
        """
        Crea un handler para logs en archivo.

        :param log_file: Ruta del archivo de log.
        :type log_file: Path
        :return: Handler configurado.
        :rtype: FileHandler
        """
        self._create_log_directory(log_file)
        handler = FileHandler(log_file)
        handler.setFormatter(logging.Formatter(self.log_format))
        return handler

    def _create_stream_handler(self) -> StreamHandler:
        """
        Crea un handler para logs en consola.

        :return: Handler configurado.
        :rtype: StreamHandler
        """
        handler = StreamHandler()
        handler.setFormatter(logging.Formatter(self.log_format))
        return handler

    def configure_logger(
        self,
        log_file: Optional[str] = None,
        log_retention_period: Optional[str] = None,
        log_backup_period: Optional[int] = None,
        name: Optional[str] = None,
    ) -> logging.Logger:
        """
        Configura y devuelve un logger basado en los parametros proporcionados.

        Este metodo configura un logger que puede registrar mensajes en consola o en un archivo,
        con opciones para rotar los logs segun un periodo especificado. Si no se proporciona
        `log_file`, el logger muestra los mensajes en consola.

        :param log_file: Ruta del archivo donde se registraran los logs. Si no se especifica,
                         los logs se muestran en consola.
        :type log_file: str, opcional
        :param log_retention_period: Periodo de rotacion de los logs. Solo se aplica si `log_file` esta definido.
                                     Debe especificarse en el formato '<n>d', '<n>w', o '<n>m', donde:
                                     - 'd' indica dias (ejemplo: '1d' para un dia),
                                     - 'w' indica semanas (ejemplo: '2w' para dos semanas),
                                     - 'm' indica meses (ejemplo: '3m' para tres meses).
        :type log_retention_period: str, opcional
        :param log_backup_period: Numero de copias de respaldo a mantener. Por defecto es 1.
                                  Solo se aplica si `log_retention_period` esta definido.
        :type log_backup_period: int, opcional
        :param name: Nombre opcional para el logger. Si no se especifica, se utiliza 'LoggingHandler'.
        :type name: str, opcional
        :return: Logger configurado segun los parametros proporcionados.
        :rtype: logging.Logger

        **Ejemplo de uso**:

        .. code-block:: python

            from logging_handler import LoggingHandler

            handler = LoggingHandler()

            # Logger en consola
            logger_console = handler.configure_logger()
            logger_console.info("Este mensaje se registra en consola.")

            # Logger en archivo con rotacion diaria y 7 backups
            logger_file = handler.configure_logger(
                log_file="app.log",
                log_retention_period="1d",
                log_backup_period=7
            )
            logger_file.info("Este mensaje se registra en un archivo con rotacion diaria.")
        """
        logger_name = name or "LoggingHandler"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)

        # Configurar el handler adecuado
        if log_file and log_retention_period:
            handler = self._create_timed_rotating_file_handler(
                log_file=Path(log_file),
                log_retention_period=log_retention_period,
                log_backup_period=log_backup_period,
            )
        elif log_file:
            handler = self._create_file_handler(Path(log_file))
        else:
            handler = self._create_stream_handler()

        self.logger.addHandler(handler)
        return self.logger

    def remove_logger_handlers(self) -> None:
        """
        Elimina todos los handlers asociados al logger de la instancia para liberar recursos.

        :raises ValueError: Si no se ha configurado ningun logger previamente.
        """
        if not self.logger:
            raise ValueError(
                "No se ha configurado ningun logger para esta instancia."
            )

        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            handler.close()

        self.logger = None
