"""
Handler personalizado para enviar logs a Grafana Loki.

Grafana Loki es un sistema de agregación de logs horizontalmente escalable,
altamente disponible y multi-tenant inspirado en Prometheus.

Características:
  - Envío de logs vía HTTP API
  - Soporte para labels personalizados (como en Prometheus)
  - Batching opcional para mejor performance
  - Manejo de errores robusto
  - Timeout configurable

API de Loki:
  POST /loki/api/v1/push
  Content-Type: application/json

  {
    "streams": [
      {
        "stream": {
          "label1": "value1",
          "label2": "value2"
        },
        "values": [
          ["<unix_epoch_timestamp_nanoseconds>", "<log_line>"]
        ]
      }
    ]
  }
"""

import json
import logging
import sys
import time
from typing import Dict, List, Optional, Tuple

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class LokiHandler(logging.Handler):
    """
    Handler personalizado para enviar logs a Grafana Loki.

    Este handler permite enviar logs a un servidor Loki utilizando su API HTTP.
    Los logs se etiquetan con labels (similares a Prometheus) para facilitar
    consultas y filtrado en Grafana.

    **Características:**
      - Envío en tiempo real o con batching
      - Labels personalizados por aplicación/servicio/entorno
      - Manejo de errores sin bloquear la aplicación
      - Timeout configurable

    **Niveles de log recomendados:**
      - ``logging.DEBUG`` (10): Depuración detallada
      - ``logging.INFO`` (20): Información general
      - ``logging.WARNING`` (30): Advertencias
      - ``logging.ERROR`` (40): Errores
      - ``logging.CRITICAL`` (50): Errores críticos

    :param url: URL del servidor Loki (ej: "http://localhost:3100").
    :type url: str
    :param labels: Diccionario de labels para identificar los logs.
                   Ejemplo: {"app": "myapp", "env": "production", "host": "server1"}
    :type labels: Dict[str, str]
    :param level: Nivel mínimo de log para enviar a Loki. Defaults to ``logging.INFO``.
    :type level: int, optional
    :param timeout: Tiempo de espera para la solicitud HTTP en segundos. Defaults to 5.
    :type timeout: int, optional
    :param batch_size: Número de logs a acumular antes de enviar (0 = sin batching). Defaults to 0.
    :type batch_size: int, optional

    :ivar url: URL del endpoint de push de Loki.
    :ivar labels: Labels asociados a este handler.
    :ivar timeout: Timeout configurado para las peticiones HTTP.
    :ivar batch_size: Tamaño del batch configurado.
    :ivar batch: Lista temporal para acumular logs (si batching está habilitado).

    Ejemplo básico:
    ---------------
    .. code-block:: python

        import logging
        from loki_handler import LokiHandler

        handler = LokiHandler(
            url="http://localhost:3100",
            labels={"app": "myapp", "env": "dev"},
            level=logging.INFO
        )

        logger = logging.getLogger("myapp")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("Aplicación iniciada")
        logger.error("Error al procesar datos")

    Ejemplo con batching:
    --------------------
    .. code-block:: python

        handler = LokiHandler(
            url="http://loki:3100",
            labels={"app": "myapp", "env": "production"},
            level=logging.INFO,
            batch_size=10  # Envía cada 10 logs
        )

    Ejemplo en producción:
    ---------------------
    .. code-block:: python

        from ctrutils.handler import LoggingHandler

        logger = LoggingHandler.production_logger(
            name="myapp",
            log_file="app.log",
            loki_url="http://loki:3100",
            loki_labels={
                "app": "myapp",
                "env": "production",
                "host": "server-01",
                "version": "1.0.0"
            }
        )

        logger.info("Aplicación en producción iniciada")
    """

    def __init__(
        self,
        url: str,
        labels: Dict[str, str],
        level: int = logging.INFO,
        timeout: int = 5,
        batch_size: int = 0,
    ) -> None:
        """
        Inicializa el LokiHandler.

        :param url: URL del servidor Loki (sin el path /loki/api/v1/push).
        :param labels: Diccionario de labels para los logs.
        :param level: Nivel mínimo de log.
        :param timeout: Timeout en segundos para las peticiones HTTP.
        :param batch_size: Número de logs a acumular antes de enviar (0 = sin batching).
        """
        super().__init__(level)

        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "El módulo 'requests' es requerido para LokiHandler. "
                "Instálalo con: pip install requests"
            )

        # Normalizar URL (remover trailing slash)
        self.url = url.rstrip("/") + "/loki/api/v1/push"
        self.labels = labels
        self.timeout = timeout
        self.batch_size = batch_size
        self.batch: List[Tuple[str, str]] = []  # [(timestamp_ns, message), ...]

    def emit(self, record: logging.LogRecord) -> None:
        """
        Envía el mensaje de log a Loki.

        Este método es llamado automáticamente por el logger cuando se registra
        un mensaje que cumple con el nivel mínimo configurado.

        Si el batching está habilitado, acumula los logs hasta alcanzar batch_size
        antes de enviarlos. Si no, envía inmediatamente.

        :param record: Registro de log a enviar.
        :type record: logging.LogRecord
        """
        try:
            log_entry = self.format(record)
            timestamp_ns = str(int(time.time() * 1e9))  # Nanosegundos

            if self.batch_size > 0:
                # Modo batching
                self.batch.append((timestamp_ns, log_entry))
                if len(self.batch) >= self.batch_size:
                    self._send_batch()
            else:
                # Modo inmediato
                self._send_to_loki([(timestamp_ns, log_entry)])

        except Exception as e:
            # No queremos que un error en logging rompa la aplicación
            print(f"Error al enviar log a Loki: {e}", file=sys.stderr)

    def _send_batch(self) -> None:
        """
        Envía el batch acumulado de logs a Loki y limpia el batch.
        """
        if self.batch:
            self._send_to_loki(self.batch)
            self.batch = []

    def _send_to_loki(self, values: List[Tuple[str, str]]) -> None:
        """
        Envía una lista de logs a Loki vía HTTP POST.

        :param values: Lista de tuplas (timestamp_nanoseconds, log_message).
        """
        payload = {
            "streams": [
                {
                    "stream": self.labels,
                    "values": values
                }
            ]
        }

        try:
            response = requests.post(
                self.url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )

            if response.status_code not in (200, 204):
                print(
                    f"Loki respondió con status {response.status_code}: {response.text}",
                    file=sys.stderr
                )

        except requests.exceptions.Timeout:
            print(
                f"Timeout al enviar logs a Loki (timeout={self.timeout}s)",
                file=sys.stderr
            )
        except requests.exceptions.RequestException as e:
            print(f"Error de red al enviar logs a Loki: {e}", file=sys.stderr)

    def flush(self) -> None:
        """
        Fuerza el envío de todos los logs pendientes en el batch.

        Este método debe ser llamado antes de cerrar la aplicación si se usa batching,
        para asegurar que todos los logs se envíen.

        Ejemplo:
        --------
        .. code-block:: python

            import atexit

            loki_handler = LokiHandler(...)
            logger.addHandler(loki_handler)

            # Asegurar que se envíen los logs pendientes al cerrar
            atexit.register(loki_handler.flush)
        """
        if self.batch_size > 0:
            self._send_batch()
        super().flush()

    def close(self) -> None:
        """
        Cierra el handler enviando los logs pendientes.
        """
        self.flush()
        super().close()


# Ejemplo de uso standalone
if __name__ == "__main__":
    # Configurar handler de Loki
    loki = LokiHandler(
        url="http://localhost:3100",
        labels={
            "app": "test_app",
            "env": "development",
            "host": "localhost"
        },
        level=logging.DEBUG
    )

    # Configurar logger
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(loki)

    # También mostrar en consola
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    logger.addHandler(console)

    # Generar logs de prueba
    logger.debug("Este es un mensaje de debug")
    logger.info("Este es un mensaje informativo")
    logger.warning("Esta es una advertencia")
    logger.error("Este es un error")
    logger.critical("Este es un error crítico")

    print("\n✅ Logs enviados a Loki. Verifica en Grafana.")
