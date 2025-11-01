"""
Módulo: logging_handler
========================

Handler principal para configuración centralizada de logging con soporte para:
- StreamHandler (consola)
- FileHandler (archivo plano)
- RotatingFileHandler (rotación por tamaño)
- TimedRotatingFileHandler (rotación por tiempo)
- LokiHandler (logs centralizados en Grafana Loki)
- TelegramBotHandler (notificaciones en tiempo real)

Características:
  - Logger único por instancia (evita duplicación)
  - Configuración flexible por nivel
  - Métodos quick_* para casos comunes
  - Soporte para múltiples handlers simultáneos
  - Gestión automática de directorios de logs

Ejemplo básico:
---------------
.. code-block:: python

    from ctrutils.handler import LoggingHandler

    # Consola rápida
    logger = LoggingHandler.quick_console_logger("myapp")
    logger.info("Hello World")

    # Archivo con rotación
    handler = LoggingHandler()
    handlers_list = [
        handler.create_stream_handler(),
        handler.create_size_rotating_file_handler(
            log_file="app.log",
            max_bytes=10*1024*1024,  # 10MB
            backup_count=5
        )
    ]
    logger = handler.add_handlers(handlers_list)

Ejemplo producción con Loki + Telegram:
---------------------------------------
.. code-block:: python

    logger = LoggingHandler.production_logger(
        name="myapp",
        log_file="production.log",
        loki_url="http://loki:3100",
        loki_labels={"app": "myapp", "env": "prod"},
        telegram_token="YOUR_TOKEN",
        telegram_chat_id="YOUR_CHAT_ID"
    )

    logger.error("Error crítico!")  # Se envía a archivo, Loki y Telegram
"""

import logging
import sys
from logging import FileHandler, StreamHandler
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import List, Optional

# Importaciones opcionales para no romper si faltan dependencias
try:
    from ..notification.loki_handler import LokiHandler
    LOKI_AVAILABLE = True
except ImportError:
    LOKI_AVAILABLE = False

try:
    from ..notification.telegram_handler import TelegramBotHandler
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False


class LoggingHandler:
    """
    Clase para configurar y manejar logs con soporte para múltiples handlers.

    Esta clase permite crear y personalizar distintos handlers para el registro de mensajes,
    incluyendo salida a consola, almacenamiento en archivos (con rotación por tamaño o por tiempo),
    envío a Grafana Loki y notificaciones vía Telegram.

    Cada instancia crea un logger único (mediante un nombre generado automáticamente o especificado)
    y desactiva la propagación de los mensajes al logger raíz, evitando duplicación.

    :param level: Nivel del logger (por defecto, ``logging.INFO``).
    :type level: int
    :param message_format: Formato de los mensajes de log.
    :type message_format: str
    :param logger_name: Nombre del logger. Si no se especifica, se genera uno único.
    :type logger_name: Optional[str]

    Ejemplo:
    --------
    .. code-block:: python

        handler = LoggingHandler(level=logging.DEBUG)
        console_handler = handler.create_stream_handler()
        logger = handler.add_handlers([console_handler])
        logger.debug("Mensaje de debug")
    """

    def __init__(
        self,
        level: int = logging.INFO,
        message_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        logger_name: Optional[str] = None,
    ):
        """
        Inicializa el LoggingHandler.

        :param level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        :param message_format: Formato de los mensajes.
        :param logger_name: Nombre único del logger.
        """
        self._level = level
        self._message_format = message_format
        self._logger_name = logger_name or f"{self.__class__.__name__}_{id(self)}"
        self.logger: Optional[logging.Logger] = logging.getLogger(self._logger_name)
        self.logger.setLevel(self._level)
        self.logger.propagate = False  # Evitar duplicación en logger raíz

    def _create_log_directory(self, log_file: Path) -> None:
        """
        Crea el directorio para el archivo de log si no existe.

        :param log_file: Ruta completa del archivo de log.
        :type log_file: Path
        """
        log_file.parent.mkdir(parents=True, exist_ok=True)

    # ==================== HANDLERS ESTÁNDAR ====================

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

        La rotación por tamaño es útil para evitar que los archivos de log crezcan demasiado
        y para mantener un número limitado de respaldos.

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
                log_file="rotating.log",
                max_bytes=10*1024*1024,  # 10MB
                backup_count=5
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

        La rotación por tiempo es útil para generar archivos de log separados por períodos
        definidos (por ejemplo, diarios o semanales).

        :param log_file: Ruta del archivo de log.
        :type log_file: str
        :param when: Unidad de tiempo para la rotación ('S'=segundos, 'M'=minutos, 'H'=horas, 'D'=días).
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
                log_file="timed.log",
                when="D",  # Diario
                interval=1,
                backup_count=7
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

    # ==================== HANDLERS ESPECIALIZADOS ====================

    def create_loki_handler(
        self,
        url: str,
        labels: Optional[dict] = None,
        level: int = logging.INFO,
        timeout: int = 5,
    ) -> "LokiHandler":
        """
        Crea un handler para enviar logs a Grafana Loki.

        Loki es un sistema de agregación de logs horizontalmente escalable,
        altamente disponible y multi-tenant inspirado en Prometheus.

        :param url: URL del servidor Loki (ej: "http://localhost:3100").
        :type url: str
        :param labels: Diccionario de labels para identificar los logs en Loki.
        :type labels: Optional[dict]
        :param level: Nivel mínimo de log para enviar a Loki.
        :type level: int
        :param timeout: Timeout para las peticiones HTTP en segundos.
        :type timeout: int
        :return: Instancia configurada de LokiHandler.
        :rtype: LokiHandler
        :raises ImportError: Si no está disponible el módulo loki_handler.

        Ejemplo:
        --------
        .. code-block:: python

            loki_handler = handler.create_loki_handler(
                url="http://loki:3100",
                labels={"app": "myapp", "env": "production"},
                level=logging.INFO
            )
        """
        if not LOKI_AVAILABLE:
            raise ImportError(
                "LokiHandler no está disponible. "
                "Asegúrate de que el módulo loki_handler está instalado correctamente."
            )

        handler = LokiHandler(url=url, labels=labels or {}, level=level, timeout=timeout)
        handler.setFormatter(logging.Formatter(self._message_format))
        return handler

    def create_telegram_handler(
        self,
        token: str,
        chat_id: str,
        level: int = logging.ERROR,
        parse_mode: str = "HTML",
        timeout: int = 20,
    ) -> "TelegramBotHandler":
        """
        Crea un handler para enviar logs a un chat o canal de Telegram.

        **Importante:**
          - Especifica el nivel mínimo de log (parámetro ``level``) para controlar
            cuándo se envían las alertas.
          - Por ejemplo, si se establece a ``logging.CRITICAL``, solo se enviarán
            notificaciones para mensajes críticos.
          - Para recibir notificaciones de diferentes niveles de forma independiente,
            crea otra instancia de LoggingHandler o agrega este handler a otro logger.

        :param token: Token de autenticación del bot de Telegram.
        :type token: str
        :param chat_id: ID del chat o canal de Telegram donde se enviarán los mensajes.
        :type chat_id: str
        :param level: Nivel mínimo de log para enviar mensajes vía Telegram (por defecto, ``logging.ERROR``).
        :type level: int
        :param parse_mode: Modo de parseo para el formato del mensaje ("HTML", "Markdown", "MarkdownV2").
        :type parse_mode: str
        :param timeout: Timeout para las peticiones HTTP en segundos.
        :type timeout: int
        :return: Instancia configurada de TelegramBotHandler.
        :rtype: TelegramBotHandler
        :raises ImportError: Si no está disponible el módulo telegram_handler.

        Ejemplo:
        --------
        .. code-block:: python

            telegram_handler = handler.create_telegram_handler(
                token="YOUR_TELEGRAM_BOT_TOKEN",
                chat_id="YOUR_TELEGRAM_CHAT_ID",
                level=logging.ERROR
            )
        """
        if not TELEGRAM_AVAILABLE:
            raise ImportError(
                "TelegramBotHandler no está disponible. "
                "Asegúrate de que el módulo telegram_handler está instalado correctamente."
            )

        handler = TelegramBotHandler(
            token=token, chat_id=chat_id, level=level, parse_mode=parse_mode, timeout=timeout
        )
        handler.setFormatter(logging.Formatter(self._message_format))
        return handler

    # ==================== GESTIÓN DE HANDLERS ====================

    def add_handlers(
        self, handlers: List[logging.Handler], logger_name: Optional[str] = None
    ) -> logging.Logger:
        """
        Agrega los handlers proporcionados a un logger y lo devuelve.

        Este método asocia los handlers a un logger identificado por el nombre de la instancia
        o uno proporcionado.

        :param handlers: Lista de instancias de logging.Handler a asociar.
        :type handlers: List[logging.Handler]
        :param logger_name: Nombre del logger. Si no se proporciona, se utiliza el nombre único de la instancia.
        :type logger_name: Optional[str]
        :return: El logger configurado con los handlers asociados.
        :rtype: logging.Logger

        Ejemplo:
        --------
        .. code-block:: python

            logger = handler.add_handlers([console_handler, file_handler])
        """
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
        :type remove_all: bool
        :param handler_types: Lista de clases de handlers a eliminar.
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

        if remove_all:
            self.logger = None

    # ==================== MÉTODOS ESTÁTICOS DE CONVENIENCIA ====================

    @staticmethod
    def quick_console_logger(name: str = "app", level: int = logging.INFO) -> logging.Logger:
        """
        Crea rápidamente un logger con salida a consola.

        :param name: Nombre del logger.
        :type name: str
        :param level: Nivel de logging.
        :type level: int
        :return: Logger configurado.
        :rtype: logging.Logger

        Ejemplo:
        --------
        .. code-block:: python

            logger = LoggingHandler.quick_console_logger("myapp", logging.DEBUG)
            logger.debug("Debug message")
        """
        handler = LoggingHandler(level=level, logger_name=name)
        return handler.add_handlers([handler.create_stream_handler()])

    @staticmethod
    def quick_file_logger(
        name: str = "app",
        log_file: str = "app.log",
        level: int = logging.INFO,
    ) -> logging.Logger:
        """
        Crea rápidamente un logger con salida a consola y archivo.

        :param name: Nombre del logger.
        :type name: str
        :param log_file: Ruta del archivo de log.
        :type log_file: str
        :param level: Nivel de logging.
        :type level: int
        :return: Logger configurado.
        :rtype: logging.Logger

        Ejemplo:
        --------
        .. code-block:: python

            logger = LoggingHandler.quick_file_logger("myapp", "app.log")
            logger.info("Info message")
        """
        handler = LoggingHandler(level=level, logger_name=name)
        return handler.add_handlers([
            handler.create_stream_handler(),
            handler.create_file_handler(log_file)
        ])

    @staticmethod
    def production_logger(
        name: str,
        log_file: str,
        loki_url: Optional[str] = None,
        loki_labels: Optional[dict] = None,
        telegram_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        level: int = logging.INFO,
    ) -> logging.Logger:
        """
        Crea un logger completo para producción con múltiples outputs.

        Incluye:
        - Archivo con rotación por tamaño (10MB, 5 backups)
        - Loki (opcional, si se proporcionan credenciales)
        - Telegram (opcional, si se proporcionan credenciales, solo errores)

        :param name: Nombre del logger.
        :type name: str
        :param log_file: Ruta del archivo de log.
        :type log_file: str
        :param loki_url: URL del servidor Loki (opcional).
        :type loki_url: Optional[str]
        :param loki_labels: Labels para Loki (opcional).
        :type loki_labels: Optional[dict]
        :param telegram_token: Token del bot de Telegram (opcional).
        :type telegram_token: Optional[str]
        :param telegram_chat_id: Chat ID de Telegram (opcional).
        :type telegram_chat_id: Optional[str]
        :param level: Nivel de logging.
        :type level: int
        :return: Logger configurado para producción.
        :rtype: logging.Logger

        Ejemplo:
        --------
        .. code-block:: python

            logger = LoggingHandler.production_logger(
                name="myapp",
                log_file="production.log",
                loki_url="http://loki:3100",
                loki_labels={"app": "myapp", "env": "prod"},
                telegram_token="YOUR_TOKEN",
                telegram_chat_id="YOUR_CHAT_ID"
            )
        """
        handler = LoggingHandler(level=level, logger_name=name)
        handlers_list = [
            handler.create_file_handler(log_file),
            handler.create_size_rotating_file_handler(
                f"{log_file}.rotating",
                max_bytes=10*1024*1024,  # 10MB
                backup_count=5
            )
        ]

        # Agregar Loki si está configurado
        if loki_url and LOKI_AVAILABLE:
            try:
                handlers_list.append(
                    handler.create_loki_handler(
                        url=loki_url,
                        labels=loki_labels or {},
                        level=level
                    )
                )
            except Exception as e:
                print(f"Warning: No se pudo configurar LokiHandler: {e}", file=sys.stderr)

        # Agregar Telegram si está configurado (solo errores)
        if telegram_token and telegram_chat_id and TELEGRAM_AVAILABLE:
            try:
                handlers_list.append(
                    handler.create_telegram_handler(
                        token=telegram_token,
                        chat_id=telegram_chat_id,
                        level=logging.ERROR
                    )
                )
            except Exception as e:
                print(f"Warning: No se pudo configurar TelegramBotHandler: {e}", file=sys.stderr)

        return handler.add_handlers(handlers_list)

    # ==================== UTILIDADES ====================

    def log_exception_and_exit(
        self,
        exception: Exception,
        exit_code: int = 1,
        context: Optional[dict] = None,
    ) -> None:
        """
        Logea una excepción con contexto y termina el proceso.

        Útil para tareas de scheduler que necesitan exit codes específicos.

        :param exception: Excepción a loguear.
        :type exception: Exception
        :param exit_code: Código de salida del proceso.
        :type exit_code: int
        :param context: Contexto adicional a incluir en el log.
        :type context: Optional[dict]

        Ejemplo:
        --------
        .. code-block:: python

            try:
                process_data()
            except Exception as e:
                handler.log_exception_and_exit(
                    e,
                    exit_code=1,
                    context={"task": "data_processing"}
                )
        """
        if not self.logger:
            raise ValueError("No se ha configurado ningún logger para esta instancia.")

        self.logger.exception(
            f"Fatal error: {exception}",
            extra=context or {},
            exc_info=True
        )
        sys.exit(exit_code)
