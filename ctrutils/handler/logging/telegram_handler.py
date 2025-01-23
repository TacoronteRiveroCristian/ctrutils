"""
Clase para enviar logs a un chat de Telegram utilizando un bot.
"""

import logging
import sys
from typing import Literal

import requests

ParseMode = Literal["HTML", "Markdown", "MarkdownV2"]


class TelegramBotHandler(logging.Handler):
    """
    Handler personalizado para enviar logs a un chat de Telegram.

    Este handler permite enviar mensajes de log a un chat o canal de Telegram
    utilizando un bot. El nivel de log y el modo de parse pueden ser configurados.
    Se recomienda utilizar los niveles predefinidos de logging para mayor claridad.

    Los niveles disponibles en el módulo logging son:
        - ``logging.NOTSET`` (0): No establece ningún nivel específico.
        - ``logging.DEBUG`` (10): Nivel para mensajes de depuración detallados.
        - ``logging.INFO`` (20): Nivel para mensajes informativos generales.
        - ``logging.WARNING`` (30): Nivel para advertencias que no detienen el programa.
        - ``logging.ERROR`` (40): Nivel para errores que afectan la funcionalidad.
        - ``logging.CRITICAL`` (50): Nivel para errores críticos que pueden detener el programa.

    :param token: Token de autenticación del bot de Telegram.
    :type token: str
    :param chat_id: ID del chat o canal de Telegram donde se enviarán los mensajes.
    :type chat_id: str
    :param level: Nivel mínimo de log para enviar mensajes. Se recomienda usar valores como ``logging.ERROR``.
                  Defaults to ``logging.ERROR``.
    :type level: int, optional
    :param parse_mode: Modo de parse para el formato del mensaje. Puede ser:
                       - ``HTML``
                       - ``Markdown``
                       - ``MarkdownV2``
                       Defaults to ``HTML``.
    :type parse_mode: ParseMode, optional
    :param timeout: Tiempo de espera para la solicitud HTTP en segundos. Defaults to 20.
    :type timeout: int, optional

    :ivar token: Token de autenticación del bot de Telegram.
    :ivar chat_id: ID del chat o canal de Telegram donde se enviarán los mensajes.
    :ivar parse_mode: Modo de parse para el formato del mensaje.
    :ivar timeout: Tiempo de espera configurado para la solicitud HTTP.

    :Example:

    >>> import logging
    >>> from mymodule import TelegramBotHandler
    >>>
    >>> handler = TelegramBotHandler(
    >>>     token="your_bot_token",
    >>>     chat_id="your_chat_id",
    >>>     level=logging.ERROR,
    >>>     parse_mode="MarkdownV2"
    >>> )
    >>> logger = logging.getLogger("my_logger")
    >>> logger.addHandler(handler)
    >>> logger.error("Este mensaje será enviado a Telegram en formato MarkdownV2")
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
        :type token: str
        :param chat_id: ID del chat o canal de Telegram donde se enviarán los mensajes.
        :type chat_id: str
        :param level: Nivel mínimo de log para enviar mensajes. Defaults to ``logging.ERROR``.
        :type level: int, optional
        :param parse_mode: Modo de parse para el formato del mensaje. Defaults to ``HTML``.
        :type parse_mode: ParseMode, optional
        :param timeout: Tiempo de espera para la solicitud HTTP en segundos. Defaults to 20.
        :type timeout: int, optional
        """
        super().__init__(level)
        self.token = token
        self.chat_id = chat_id
        self.parse_mode = parse_mode
        self.timeout = timeout

    def emit(self, record: logging.LogRecord) -> None:
        """
        Envía el mensaje de log a Telegram.

        Este método es llamado automáticamente por el logger cuando se registra
        un mensaje que cumple con el nivel mínimo configurado.

        :param record: Registro de log a enviar.
        :type record: logging.LogRecord
        """
        log_entry = self.format(record)  # Formatea el registro del log
        payload = {
            "chat_id": self.chat_id,
            "text": log_entry,
            "parse_mode": self.parse_mode,
        }
        try:
            # Enviar mensaje a Telegram usando requests
            requests.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                data=payload,
                timeout=self.timeout,
            )
        except Exception as e:
            # Manejo de errores al enviar el mensaje
            print(f"Error al enviar mensaje a Telegram: {e}", file=sys.stderr)
