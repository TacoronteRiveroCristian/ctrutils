"""
Módulo de gestión de logging con múltiples handlers.

Este módulo proporciona la clase LoggingHandler para configurar y gestionar
sistemas de logging con soporte para múltiples handlers simultáneos.

Classes:
    LoggingHandler: Gestor de configuración de logging con factory methods para
                   crear diferentes tipos de handlers (stream, file, rotating, etc.).

Supported Handlers:
    - Stream (console): Salida a stdout/stderr con colores opcionales
    - File: Escritura a archivo simple
    - Rotating File (size): Rotación por tamaño con backup automático
    - Timed Rotating File: Rotación por tiempo (diario, semanal, etc.)
    - Loki: Envío a Grafana Loki para centralización
    - Telegram: Notificaciones a Telegram para alertas críticas

Examples:
    >>> from ctrutils.handler.logging import LoggingHandler
    >>> import logging
    >>>
    >>> # Logger básico con consola y archivo rotativo
    >>> logger = LoggingHandler(logger_name='mi_app', level=logging.INFO)
    >>> logger.add_handlers([
    ...     logger.create_stream_handler(),
    ...     logger.create_rotating_file_handler(
    ...         filename='app.log',
    ...         max_bytes=10*1024*1024,  # 10MB
    ...         backup_count=5
    ...     )
    ... ])
    >>> logger.info("Aplicación iniciada")

See Also:
    - Documentación: ctrutils/handler/README.md
"""

from .logging_handler import LoggingHandler

__all__ = ["LoggingHandler"]
