"""
Handler Module
==============

Módulo centralizado para gestión de logging con soporte para:
- Logging estándar (consola, archivos, rotación)
- Grafana Loki (logs centralizados)
- Telegram (notificaciones)

Ejemplo básico:
---------------
>>> from ctrutils.handler import LoggingHandler
>>> logger = LoggingHandler.quick_console_logger("myapp")
>>> logger.info("Hello World")

Ejemplo con Loki:
-----------------
>>> from ctrutils.handler import LoggingHandler, LokiHandler
>>> handler = LoggingHandler()
>>> loki = handler.create_loki_handler(
...     url="http://localhost:3100",
...     labels={"app": "myapp", "env": "production"}
... )
>>> logger = handler.add_handlers([loki])

Ejemplo con Telegram:
---------------------
>>> handler = LoggingHandler()
>>> telegram = handler.create_telegram_handler(
...     token="YOUR_BOT_TOKEN",
...     chat_id="YOUR_CHAT_ID",
...     level=logging.ERROR
... )
>>> logger = handler.add_handlers([telegram])
"""

from .logging.logging_handler import LoggingHandler
from .notification.loki_handler import LokiHandler
from .notification.telegram_handler import TelegramBotHandler

__all__ = [
    "LoggingHandler",
    "LokiHandler",
    "TelegramBotHandler",
]
