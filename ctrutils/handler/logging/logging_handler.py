"""
Módulo: logging_handler
========================

Este módulo provee la clase LoggingHandler, que facilita la configuración y manejo de logs con soporte para múltiples handlers,
entre ellos salida a consola, almacenamiento en archivos (incluyendo opciones de rotación por tamaño y por tiempo) y notificaciones vía Telegram.

Características especiales:
  - **File Rotation:** Permite la configuración de file rotation (por tamaño o por tiempo) para limitar el tamaño de los archivos de log y mantener respaldos.
  - **Telegram Notifications:** Se puede configurar un handler para enviar alertas a Telegram. Es muy importante especificar el nivel de log en el handler de Telegram para
    controlar la criticidad de los mensajes que se envían. Por ejemplo, si se establece el nivel a `logging.CRITICAL`, solo se enviarán notificaciones de mensajes críticos.
    Si se desea recibir notificaciones de otros niveles (como ERROR o WARNING) de forma independiente, se recomienda crear otra instancia de LoggingHandler (o agregar el handler a
    otro logger) con un nombre distinto y configurar un nivel de notificación específico.

Ejemplo de uso:
---------------
.. code-block:: python

    import logging
    from logging_handler import LoggingHandler

    # Crear una instancia principal para logs generales (p.ej., en consola y archivos)
    handler = LoggingHandler(
        level=logging.DEBUG,
        message_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Handlers para salida a consola y archivo simple
    console_handler = handler.create_stream_handler()
    file_handler = handler.create_file_handler("app.log")

    # Handler para rotación basada en tamaño (File Rotation)
    rotating_handler = handler.create_size_rotating_file_handler(
        log_file="rotating.log", max_bytes=1024 * 1024, backup_count=5
    )

    # Handler para rotación basada en tiempo (File Rotation)
    timed_handler = handler.create_timed_rotating_file_handler(
        log_file="timed.log", when="D", interval=1, backup_count=7
    )

    # Handler para enviar alertas vía Telegram.
    # Importante: Ajuste el nivel según la criticidad deseada. Por ejemplo,
    # si se establece a logging.CRITICAL, solo se enviarán mensajes críticos.
    # Para notificaciones de otros niveles, se recomienda configurar otro logger o instancia.
    telegram_handler = handler.create_telegram_handler(
        token="YOUR_TELEGRAM_BOT_TOKEN",
        chat_id="YOUR_TELEGRAM_CHAT_ID",
        level=logging.ERROR  # Cambie este nivel según sus necesidades de alerta
    )

    # Agregar todos los handlers al logger
    logger = handler.add_handlers([
        console_handler,
        file_handler,
        rotating_handler,
        timed_handler,
        telegram_handler
    ])

    # Generar logs de prueba
    logger.debug("Mensaje de depuración")
    logger.info("Mensaje informativo")
    logger.error("Mensaje de error")
    logger.critical("Mensaje crítico")


:mod:`logging_handler` es ideal para aplicaciones que requieren un registro de logs centralizado,
con soporte para archivo rotativo y alertas inmediatas vía Telegram.
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

    Esta clase permite crear y personalizar distintos handlers para el registro de mensajes,
    incluyendo salida a consola, almacenamiento en archivos (con rotación por tamaño o por tiempo) y
    notificaciones vía Telegram. Cada instancia crea un logger único (mediante un nombre generado automáticamente
    o especificado) y desactiva la propagación de los mensajes al logger raíz, evitando duplicación.

    .. note::

       **File Rotation:** Los métodos ``create_size_rotating_file_handler`` y ``create_timed_rotating_file_handler``
       permiten configurar la rotación de archivos de log. Esto es fundamental para aplicaciones de larga duración o con
       gran volumen de logs, ya que evita que los archivos de log crezcan sin control.

       **Telegram Notifications:** El método ``create_telegram_handler`` permite enviar alertas a Telegram. Es muy importante
       especificar correctamente el nivel de log al crear este handler. Por ejemplo, si se configura el nivel a
       ``logging.CRITICAL``, solo se enviarán notificaciones para mensajes críticos. Si se desea recibir notificaciones
       para otros niveles (como ERROR o WARNING) de forma independiente, lo recomendable es:
         - Crear otra instancia de ``LoggingHandler`` exclusiva para Telegram, o
         - Agregar el handler de Telegram a un logger con un nombre distinto y configurar el nivel de notificación deseado.

    Ejemplo de uso:
    --------------
    .. code-block:: python

        import logging
        from logging_handler import LoggingHandler

        # Instancia para logs generales
        handler = LoggingHandler(level=logging.DEBUG, message_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        console_handler = handler.create_stream_handler()
        file_handler = handler.create_file_handler("app.log")
        rotating_handler = handler.create_size_rotating_file_handler("rotating.log", max_bytes=1024*1024, backup_count=5)
        timed_handler = handler.create_timed_rotating_file_handler("timed.log", when="D", interval=1, backup_count=7)

        # Instancia para notificaciones vía Telegram (ajuste el nivel según la criticidad deseada)
        telegram_handler = handler.create_telegram_handler(token="YOUR_TELEGRAM_BOT_TOKEN", chat_id="YOUR_TELEGRAM_CHAT_ID", level=logging.ERROR)

        # Agregar todos los handlers al logger
        logger = handler.add_handlers([console_handler, file_handler, rotating_handler, timed_handler, telegram_handler])
        logger.info("Logger configurado con múltiples handlers")

    :param level: Nivel del logger (por defecto, ``logging.INFO``).
    :type level: int
    :param message_format: Formato de los mensajes de log, que se aplicará a todos los handlers.
    :type message_format: str
    :param logger_name: Nombre del logger. Si no se especifica, se genera un nombre único basado en la clase y el id de la instancia.
    :type logger_name: Optional[str]
    """

    def __init__(
        self,
        level: int = logging.INFO,
        message_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        logger_name: Optional[str] = None,
    ):
        self._level = level
        self._message_format = message_format

        # Genera un nombre único si no se especifica uno
        self._logger_name = logger_name or f"{self.__class__.__name__}_{id(self)}"
        self.logger: Optional[logging.Logger] = logging.getLogger(self._logger_name)
        self.logger.setLevel(self._level)
        # Desactivar la propagación para evitar duplicación en el logger raíz
        self.logger.propagate = False

    def _create_log_directory(self, log_file: Path) -> None:
        """
        Crea el directorio para el archivo de log si no existe.

        :param log_file: Ruta completa del archivo de log.
        :type log_file: Path

        Ejemplo:
        --------
        .. code-block:: python

            handler._create_log_directory(Path("logs/app.log"))
        """
        log_file.parent.mkdir(parents=True, exist_ok=True)

    def create_stream_handler(self) -> StreamHandler:
        """
        Crea un handler para la salida de logs a la consola.

        :return: Instancia configurada de StreamHandler.
        :rtype: StreamHandler

        Ejemplo:
        --------
        .. code-block:: python

            console_handler = handler.create_stream_handler()
        """
        handler = StreamHandler()
        handler.setLevel(self._level)
        handler.setFormatter(logging.Formatter(self._message_format))
        return handler

    def create_file_handler(self, log_file: str) -> FileHandler:
        """
        Crea un handler para guardar los logs en un archivo plano.

        :param log_file: Ruta del archivo donde se almacenarán los logs.
        :type log_file: str
        :return: Instancia configurada de FileHandler.
        :rtype: FileHandler

        Ejemplo:
        --------
        .. code-block:: python

            file_handler = handler.create_file_handler("app.log")
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
        Crea un handler para guardar los logs en un archivo con rotación basada en tamaño.

        La rotación por tamaño es útil para evitar que los archivos de log crezcan demasiado y para mantener un número
        limitado de respaldos. Se especifica el tamaño máximo en bytes y el número de archivos de respaldo a conservar.

        :param log_file: Ruta del archivo de log.
        :type log_file: str
        :param max_bytes: Tamaño máximo en bytes antes de que se produzca la rotación.
        :type max_bytes: int
        :param backup_count: Número máximo de archivos de respaldo a mantener.
        :type backup_count: int
        :return: Instancia configurada de RotatingFileHandler.
        :rtype: RotatingFileHandler

        Ejemplo:
        --------
        .. code-block:: python

            rotating_handler = handler.create_size_rotating_file_handler(
                log_file="rotating.log", max_bytes=1024*1024, backup_count=5
            )
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
        Crea un handler para guardar los logs en un archivo con rotación basada en tiempo.

        La rotación por tiempo es útil para generar archivos de log separados por períodos definidos (por ejemplo, diarios o
        semanales), lo que facilita la organización y el análisis de logs en intervalos regulares.

        :param log_file: Ruta del archivo de log.
        :type log_file: str
        :param when: Unidad de tiempo para la rotación (por ejemplo, 'S' para segundos, 'M' para minutos, 'H' para horas, 'D' para días).
        :type when: str
        :param interval: Intervalo de tiempo para la rotación.
        :type interval: int
        :param backup_count: Número máximo de archivos de respaldo a mantener.
        :type backup_count: int
        :return: Instancia configurada de TimedRotatingFileHandler.
        :rtype: TimedRotatingFileHandler

        Ejemplo:
        --------
        .. code-block:: python

            timed_handler = handler.create_timed_rotating_file_handler(
                log_file="timed.log", when="D", interval=1, backup_count=7
            )
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
        Crea un handler para enviar logs a un chat o canal de Telegram.

        **Importante sobre Telegram:**
          - Es crucial especificar el nivel mínimo de log (parámetro ``level``) para controlar cuándo se envían las alertas.
            Por ejemplo, si se establece a ``logging.CRITICAL``, solo se enviarán notificaciones para mensajes críticos.
          - Si se desea recibir notificaciones para niveles distintos (por ejemplo, ERROR o WARNING) de forma independiente,
            se recomienda crear otra instancia de LoggingHandler o agregar este handler a otro logger con un nombre distinto y
            configurar el nivel de notificación apropiado.

        :param token: Token de autenticación del bot de Telegram.
        :type token: str
        :param chat_id: ID del chat o canal de Telegram donde se enviarán los mensajes.
        :type chat_id: str
        :param level: Nivel mínimo de log para enviar mensajes vía Telegram (por defecto, ``logging.ERROR``).
        :type level: int, opcional
        :param parse_mode: Modo de parseo para el formato del mensaje (por ejemplo, "HTML" o "Markdown").
                           Por defecto es "HTML".
        :type parse_mode: ParseMode, opcional
        :return: Instancia configurada de TelegramBotHandler.
        :rtype: TelegramBotHandler

        Ejemplo:
        --------
        .. code-block:: python

            telegram_handler = handler.create_telegram_handler(
                token="YOUR_TELEGRAM_BOT_TOKEN",
                chat_id="YOUR_TELEGRAM_CHAT_ID",
                level=logging.ERROR
            )
        """
        handler = TelegramBotHandler(token, chat_id, level, parse_mode)
        handler.setFormatter(logging.Formatter(self._message_format))
        return handler

    def add_handlers(
        self, handlers: List[logging.Handler], logger_name: Optional[str] = None
    ) -> logging.Logger:
        """
        Agrega los handlers proporcionados a un logger y lo devuelve.

        Este método asocia los handlers a un logger identificado por el nombre de la instancia o uno
        proporcionado. Si se desea encapsular configuraciones de notificación (por ejemplo, Telegram) de manera
        independiente, es recomendable utilizar un nombre de logger distinto al de la instancia original.

        :param handlers: Lista de instancias de logging.Handler a asociar.
        :type handlers: List[logging.Handler]
        :param logger_name: Nombre del logger. Si no se proporciona, se utiliza el nombre único de la instancia.
        :type logger_name: Optional[str], opcional
        :return: El logger configurado con los handlers asociados.
        :rtype: logging.Logger

        Ejemplo:
        --------
        .. code-block:: python

            logger = handler.add_handlers([console_handler, file_handler])
        """
        # Usa el nombre de la instancia o el proporcionado
        logger_name = logger_name or self._logger_name
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
        Elimina uno o varios handlers asociados al logger de la instancia.

        :param remove_all: Si es True, elimina todos los handlers asociados al logger.
                           Si es False, elimina únicamente aquellos handlers cuyos tipos estén en la lista ``handler_types``.
        :type remove_all: bool
        :param handler_types: Lista de clases de handlers a eliminar (por ejemplo, ``[StreamHandler, FileHandler]``).
                              Se ignora si ``remove_all`` es True.
        :type handler_types: Optional[List[type]]
        :raises ValueError: Si no se ha configurado ningún logger previamente.

        Ejemplo:
        --------
        .. code-block:: python

            # Eliminar todos los handlers
            handler.remove_handlers(remove_all=True)

            # Eliminar solo los handlers de tipo StreamHandler
            handler.remove_handlers(remove_all=False, handler_types=[StreamHandler])
        """
        if not self.logger:
            raise ValueError("No se ha configurado ningún logger para esta instancia.")

        if remove_all:
            for h in self.logger.handlers[:]:
                self.logger.removeHandler(h)
                h.close()
        elif handler_types:
            for h in self.logger.handlers[:]:
                if isinstance(h, tuple(handler_types)):
                    self.logger.removeHandler(h)
                    h.close()

        # Si se eliminan todos los handlers, reinicia la instancia del logger
        if remove_all:
            self.logger = None
