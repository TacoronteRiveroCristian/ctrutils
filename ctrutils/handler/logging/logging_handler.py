"""
Clase para configurar y manejar logs con soporte para multiples handlers.
"""

import logging
from logging import FileHandler, StreamHandler
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import List, Optional

from .telegram_handler import ParseMode, TelegramBotHandler


class LoggingHandler:
    """
    Clase para configurar y manejar logs con soporte para múltiples handlers.

    Permite crear y personalizar handlers para consola, archivos, rotación basada en tiempo
    o en tamaño, y asociarlos a un logger.

    Ejemplo de uso:

    .. code-block:: python

        from logging_handler import LoggingHandler

        handler = LoggingHandler(level=logging.DEBUG, message_format="%(asctime)s - %(message)s")

        # Crear handlers
        console_handler = handler.create_stream_handler()
        file_handler = handler.create_file_handler("app.log")
        rotating_handler = handler.create_rotating_file_handler("rotating.log", max_bytes=1024*1024, backup_count=5)

        # Crear el logger con los handlers
        logger = handler.add_handlers([console_handler, file_handler, rotating_handler])
        logger.info("Logger configurado con múltiples handlers")
    """

    def __init__(
        self,
        level: int = logging.INFO,
        message_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    ):
        """
        Inicializa una instancia de LoggingHandler con configuraciones predeterminadas.

        :param level: Nivel del logger (por defecto, logging.INFO).
        :type level: int
        :param message_format: Formato de los mensajes de log.
        :type message_format: str
        """
        self._level = level
        self._message_format = message_format
        self.logger: Optional[logging.Logger] = None

    def _create_log_directory(self, log_file: Path) -> None:
        """
        Crea la carpeta para el archivo de log si no existe.

        :param log_file: Ruta del archivo de log.
        :type log_file: Path
        """
        log_file.parent.mkdir(parents=True, exist_ok=True)

    def create_stream_handler(self) -> StreamHandler:
        """
        Crea un handler para logs en consola.

        :return: StreamHandler configurado.
        :rtype: StreamHandler
        """
        handler = StreamHandler()
        handler.setLevel(self._level)
        handler.setFormatter(logging.Formatter(self._message_format))
        return handler

    def create_file_handler(self, log_file: str) -> FileHandler:
        """
        Crea un handler para logs en un archivo.

        :param log_file: Ruta del archivo de log.
        :type log_file: str
        :return: FileHandler configurado.
        :rtype: FileHandler
        """
        log_path = Path(log_file)
        self._create_log_directory(log_path)
        handler = FileHandler(log_path)
        handler.setLevel(self._level)
        handler.setFormatter(logging.Formatter(self._message_format))
        return handler

    def create_size_rotating_file_handler(
        self, log_file: str, max_bytes: int, backup_count: int
    ) -> RotatingFileHandler:
        """
        Crea un handler para logs en un archivo con rotación basada en tamaño.

        :param log_file: Ruta del archivo de log.
        :type log_file: str
        :param max_bytes: Tamaño máximo en bytes antes de rotar el archivo.
        :type max_bytes: int
        :param backup_count: Número máximo de archivos de respaldo a mantener.
        :type backup_count: int
        :return: RotatingFileHandler configurado.
        :rtype: RotatingFileHandler
        """
        log_path = Path(log_file)
        self._create_log_directory(log_path)
        handler = RotatingFileHandler(
            log_path, maxBytes=max_bytes, backupCount=backup_count
        )
        handler.setLevel(self._level)
        handler.setFormatter(logging.Formatter(self._message_format))
        return handler

    def create_timed_rotating_file_handler(
        self, log_file: str, when: str, interval: int, backup_count: int
    ) -> TimedRotatingFileHandler:
        """
        Crea un handler para logs en un archivo con rotación basada en tiempo.

        :param log_file: Ruta del archivo de log.
        :type log_file: str
        :param when: Unidad de tiempo para la rotación (ejemplo: 'D' para días, 'H' para horas).
        :type when: str
        :param interval: Intervalo de tiempo para la rotación.
        :type interval: int
        :param backup_count: Número máximo de archivos de respaldo a mantener.
        :type backup_count: int
        :return: TimedRotatingFileHandler configurado.
        :rtype: TimedRotatingFileHandler
        """
        log_path = Path(log_file)
        self._create_log_directory(log_path)
        handler = TimedRotatingFileHandler(
            log_path, when=when, interval=interval, backupCount=backup_count
        )
        handler.setLevel(self._level)
        handler.setFormatter(logging.Formatter(self._message_format))
        return handler

    def create_telegram_handler(
        self,
        token: str,
        chat_id: str,
        level: int = logging.ERROR,
        parse_mode: ParseMode = "HTML",
    ) -> TelegramBotHandler:
        """
        Crea un handler para enviar logs a Telegram.

        :param token: Token de autenticacion del bot de Telegram.
        :type token: str
        :param chat_id: ID del chat o canal de Telegram donde se enviaran los mensajes.
        :type chat_id: str
        :param level: Nivel minimo de log para enviar mensajes, defaults to logging.ERROR
        :type level: int, optional
        :param parse_mode: Modo de parse para el formato del mensaje, defaults to "HTML"
        :type parse_mode: ParseMode, optional
        :return: TelegramBotHandler configurado.
        :rtype: TelegramBotHandler
        """
        handler = TelegramBotHandler(token, chat_id, level, parse_mode)
        handler.setFormatter(logging.Formatter(self._message_format))
        return handler

    def add_handlers(
        self, handlers: List[logging.Handler], name: Optional[str] = None
    ) -> logging.Logger:
        """
        Agrega los handlers proporcionados a un logger y lo devuelve.

        :param handlers: Lista de handlers a asociar al logger.
        :type handlers: List[logging.Handler]
        :param name: Nombre opcional para el logger. Si no se especifica, se utiliza 'LoggingHandler'.
        :type name: str, opcional
        :return: Logger configurado con los handlers proporcionados.
        :rtype: logging.Logger
        """
        logger_name = name or "LoggingHandler"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(self._level)

        for handler in handlers:
            self.logger.addHandler(handler)

        return self.logger

    def remove_handlers(
        self,
        remove_all: bool = True,
        handler_types: Optional[List[type]] = None,
    ) -> None:
        """
        Elimina uno o varios handlers asociados al logger.

        :param remove_all: Si es True, elimina todos los handlers. Si es False, elimina solo los especificados en handler_types.
        :type remove_all: bool
        :param handler_types: Lista de tipos de handlers a eliminar (por ejemplo, [StreamHandler, FileHandler]).
                              Se ignora si remove_all es True.
        :type handler_types: List[type], opcional
        :raises ValueError: Si no se ha configurado ningún logger previamente.
        """
        if not self.logger:
            raise ValueError("No se ha configurado ningún logger para esta instancia.")

        if remove_all:
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)
                handler.close()
        elif handler_types:
            for handler in self.logger.handlers[:]:
                if handler in handler_types:
                    self.logger.removeHandler(handler)
                    handler.close()

        # Si se eliminan todos los handlers, reinicia la instancia del logger
        if remove_all:
            self.logger = None
