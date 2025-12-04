"""
Módulo de handlers de notificación para logging.

Este módulo proporciona handlers personalizados de logging para enviar logs
y notificaciones a servicios externos como Grafana Loki y Telegram.

Classes:
    LokiHandler: Handler para enviar logs a Grafana Loki con batching automático.
    TelegramBotHandler: Handler para enviar notificaciones a Telegram con formato.

Features:
    - Loki: Batching automático, labels personalizables, flush manual
    - Telegram: Emojis por nivel de log, formato Markdown, rate limiting

Examples:
    Loki Handler para centralización de logs:

    >>> from ctrutils.handler.notification import LokiHandler
    >>> import logging
    >>>
    >>> logger = logging.getLogger('app')
    >>> loki_handler = LokiHandler(
    ...     url='http://localhost:3100',
    ...     labels={'app': 'mi_app', 'env': 'prod'},
    ...     batch_size=100
    ... )
    >>> logger.addHandler(loki_handler)
    >>> logger.info("Log centralizado en Loki")

    Telegram Handler para alertas críticas:

    >>> from ctrutils.handler.notification import TelegramBotHandler
    >>> import logging
    >>>
    >>> logger = logging.getLogger('alertas')
    >>> telegram_handler = TelegramBotHandler(
    ...     token='BOT_TOKEN',
    ...     chat_id='CHAT_ID',
    ...     level=logging.ERROR  # Solo errores y críticos
    ... )
    >>> logger.addHandler(telegram_handler)
    >>> logger.error("Error crítico detectado!")

See Also:
    - Documentación: ctrutils/handler/README.md
"""

from .loki_handler import LokiHandler
from .telegram_handler import TelegramBotHandler

__all__ = ["LokiHandler", "TelegramBotHandler"]
