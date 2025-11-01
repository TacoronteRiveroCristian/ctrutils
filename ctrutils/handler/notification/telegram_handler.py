"""
Handler personalizado para enviar logs a un chat de Telegram.

Permite enviar notificaciones de log a Telegram Bot API para alertas
en tiempo real de errores críticos, warnings, etc.

Telegram Bot API:
  POST https://api.telegram.org/bot<token>/sendMessage

  {
    "chat_id": "...",
    "text": "...",
    "parse_mode": "HTML"  // o "Markdown", "MarkdownV2"
  }
"""

import logging
import sys
from typing import Literal

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

ParseMode = Literal["HTML", "Markdown", "MarkdownV2"]


class TelegramBotHandler(logging.Handler):
    """
    Handler personalizado para enviar logs a un chat de Telegram.

    Este handler permite enviar mensajes de log a un chat o canal de Telegram
    utilizando un bot. El nivel de log y el modo de parse pueden ser configurados.
    Se recomienda utilizar los niveles predefinidos de logging para mayor claridad.

    **Niveles de log disponibles:**
      - ``logging.DEBUG`` (10): Mensajes de depuración detallados
      - ``logging.INFO`` (20): Mensajes informativos generales
      - ``logging.WARNING`` (30): Advertencias que no detienen el programa
      - ``logging.ERROR`` (40): Errores que afectan la funcionalidad
      - ``logging.CRITICAL`` (50): Errores críticos que pueden detener el programa

    **Parse Modes:**
      - ``HTML``: Permite usar HTML básico (<b>, <i>, <code>, <pre>)
      - ``Markdown``: Markdown básico (legacy)
      - ``MarkdownV2``: Markdown mejorado con más opciones

    **Importante:**
      - Configura el nivel apropiado para evitar spam en Telegram
      - Por defecto envía solo ``ERROR`` y superiores
      - Para testing usa un chat privado, no grupos

    :param token: Token de autenticación del bot de Telegram.
    :type token: str
    :param chat_id: ID del chat o canal de Telegram donde se enviarán los mensajes.
    :type chat_id: str
    :param level: Nivel mínimo de log para enviar mensajes. Defaults to ``logging.ERROR``.
    :type level: int, optional
    :param parse_mode: Modo de parse para el formato del mensaje. Defaults to ``HTML``.
    :type parse_mode: ParseMode, optional
    :param timeout: Tiempo de espera para la solicitud HTTP en segundos. Defaults to 20.
    :type timeout: int, optional

    :ivar token: Token de autenticación del bot de Telegram.
    :ivar chat_id: ID del chat o canal de Telegram.
    :ivar parse_mode: Modo de parse configurado.
    :ivar timeout: Timeout configurado para las peticiones HTTP.

    Ejemplo básico:
    ---------------
    .. code-block:: python

        import logging
        from telegram_handler import TelegramBotHandler

        handler = TelegramBotHandler(
            token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
            chat_id="123456789",
            level=logging.ERROR,
            parse_mode="HTML"
        )

        logger = logging.getLogger("my_logger")
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)

        logger.error("Este mensaje será enviado a Telegram")

    Ejemplo con formato HTML:
    ------------------------
    .. code-block:: python

        handler = TelegramBotHandler(
            token="YOUR_TOKEN",
            chat_id="YOUR_CHAT_ID",
            parse_mode="HTML"
        )

        logger = logging.getLogger("app")
        logger.addHandler(handler)

        # Los mensajes pueden incluir HTML básico
        logger.error("<b>Error crítico:</b> <code>División por cero</code>")

    Ejemplo en producción:
    ---------------------
    .. code-block:: python

        from ctrutils.handler import LoggingHandler

        logger = LoggingHandler.production_logger(
            name="myapp",
            log_file="production.log",
            telegram_token="YOUR_TOKEN",
            telegram_chat_id="YOUR_CHAT_ID"
        )

        # Solo errores y críticos se envían a Telegram
        logger.info("Info - NO se envía a Telegram")
        logger.error("Error - SÍ se envía a Telegram")
    """

    def __init__(
        self,
        token: str,
        chat_id: str,
        level: int = logging.ERROR,
        parse_mode: ParseMode = "HTML",
        timeout: int = 20,
    ) -> None:
        """
        Inicializa el TelegramBotHandler.

        :param token: Token de autenticación del bot de Telegram.
        :param chat_id: ID del chat o canal de Telegram.
        :param level: Nivel mínimo de log para enviar mensajes.
        :param parse_mode: Modo de parse del mensaje ("HTML", "Markdown", "MarkdownV2").
        :param timeout: Timeout en segundos para las peticiones HTTP.
        """
        super().__init__(level)

        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "El módulo 'requests' es requerido para TelegramBotHandler. "
                "Instálalo con: pip install requests"
            )

        self.token = token
        self.chat_id = chat_id
        self.parse_mode = parse_mode
        self.timeout = timeout
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def emit(self, record: logging.LogRecord) -> None:
        """
        Envía el mensaje de log a Telegram.

        Este método es llamado automáticamente por el logger cuando se registra
        un mensaje que cumple con el nivel mínimo configurado.

        El mensaje incluye:
        - Emoji según el nivel (ℹ️ INFO, ⚠️ WARNING, ❌ ERROR, 🚨 CRITICAL)
        - Timestamp
        - Nombre del logger
        - Nivel
        - Mensaje formateado

        :param record: Registro de log a enviar.
        :type record: logging.LogRecord
        """
        try:
            log_entry = self.format(record)

            # Agregar emoji según el nivel
            emoji = self._get_emoji_for_level(record.levelname)
            message = f"{emoji} {log_entry}"

            # Limitar longitud del mensaje (Telegram max: 4096 caracteres)
            if len(message) > 4000:
                message = message[:3997] + "..."

            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": self.parse_mode,
            }

            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code != 200:
                print(
                    f"Telegram respondió con status {response.status_code}: {response.text}",
                    file=sys.stderr
                )

        except requests.exceptions.Timeout:
            print(
                f"Timeout al enviar mensaje a Telegram (timeout={self.timeout}s)",
                file=sys.stderr
            )
        except requests.exceptions.RequestException as e:
            print(f"Error de red al enviar mensaje a Telegram: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Error inesperado al enviar mensaje a Telegram: {e}", file=sys.stderr)

    def _get_emoji_for_level(self, levelname: str) -> str:
        """
        Retorna un emoji apropiado según el nivel de log.

        :param levelname: Nombre del nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        :return: Emoji representativo.
        """
        emojis = {
            "DEBUG": "🐛",
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🚨",
        }
        return emojis.get(levelname, "📝")


# Ejemplo de uso standalone
if __name__ == "__main__":
    import os

    # Obtener credenciales de variables de entorno
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    if not TOKEN or not CHAT_ID:
        print("Error: Define TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en las variables de entorno")
        print("\nEjemplo:")
        print("  export TELEGRAM_BOT_TOKEN='123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'")
        print("  export TELEGRAM_CHAT_ID='123456789'")
        sys.exit(1)

    # Configurar handler de Telegram
    telegram = TelegramBotHandler(
        token=TOKEN,
        chat_id=CHAT_ID,
        level=logging.INFO,
        parse_mode="HTML"
    )

    # Configurar logger
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)
    logger.addHandler(telegram)

    # También mostrar en consola
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    logger.addHandler(console)

    # Generar logs de prueba
    print("Enviando logs de prueba a Telegram...\n")

    logger.info("Este es un mensaje <b>informativo</b>")
    logger.warning("Esta es una <i>advertencia</i>")
    logger.error("Este es un <code>error</code>")
    logger.critical("Este es un error <b>CRÍTICO</b>")

    print("\n✅ Logs enviados a Telegram. Verifica tu chat.")
