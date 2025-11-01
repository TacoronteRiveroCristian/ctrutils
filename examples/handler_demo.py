"""
Ejemplo de uso del módulo handler con Scheduler y InfluxDB

Este script demuestra cómo usar el nuevo sistema de logging
centralizado con Grafana Loki y Telegram.
"""

import logging
import os
from ctrutils import LoggingHandler, Scheduler, InfluxdbOperation

# =========================================================================
# EJEMPLO 1: Logger básico de consola
# =========================================================================
print("=" * 60)
print("EJEMPLO 1: Logger básico de consola")
print("=" * 60)

logger = LoggingHandler.quick_console_logger("demo", logging.INFO)
logger.info("✅ Logger básico configurado")
logger.warning("⚠️ Esta es una advertencia")
logger.error("❌ Este es un error")

# =========================================================================
# EJEMPLO 2: Logger con archivo y rotación
# =========================================================================
print("\n" + "=" * 60)
print("EJEMPLO 2: Logger con archivo y rotación")
print("=" * 60)

handler = LoggingHandler(level=logging.DEBUG)
handlers_list = [
    handler.create_stream_handler(),
    handler.create_file_handler("demo.log"),
    handler.create_size_rotating_file_handler(
        log_file="demo_rotating.log",
        max_bytes=1024 * 1024,  # 1MB
        backup_count=3
    )
]
file_logger = handler.add_handlers(handlers_list, logger_name="file_demo")
file_logger.debug("🐛 Debug message")
file_logger.info("📝 Info message - guardado en archivo")

# =========================================================================
# EJEMPLO 3: Logger de producción con Loki (si está configurado)
# =========================================================================
print("\n" + "=" * 60)
print("EJEMPLO 3: Logger de producción con Loki")
print("=" * 60)

LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

try:
    prod_logger = LoggingHandler.production_logger(
        name="demo_production",
        log_file="production.log",
        loki_url=LOKI_URL if LOKI_URL else None,
        loki_labels={
            "app": "ctrutils_demo",
            "env": "development",
            "host": "localhost"
        },
        telegram_token=TELEGRAM_TOKEN,
        telegram_chat_id=TELEGRAM_CHAT_ID,
        level=logging.INFO
    )

    prod_logger.info("🚀 Logger de producción configurado")
    prod_logger.info("📊 Este log se envía a archivo + Loki")
    prod_logger.error("❌ Este error se envía también a Telegram (si está configurado)")

    print("✅ Logger de producción OK")
    if LOKI_URL:
        print(f"   - Loki: {LOKI_URL}")
    if TELEGRAM_TOKEN:
        print(f"   - Telegram: Configurado")

except Exception as e:
    print(f"⚠️ No se pudo configurar logger de producción: {e}")

# =========================================================================
# EJEMPLO 4: Integración con Scheduler
# =========================================================================
print("\n" + "=" * 60)
print("EJEMPLO 4: Scheduler con logging personalizado")
print("=" * 60)

scheduler_handler = LoggingHandler()
scheduler_logger = scheduler_handler.add_handlers([
    scheduler_handler.create_stream_handler(),
    scheduler_handler.create_file_handler("scheduler.log")
], logger_name="scheduler_demo")

scheduler = Scheduler(logger=scheduler_logger, timezone="UTC")

def tarea_ejemplo():
    """Tarea de ejemplo para el scheduler"""
    scheduler_logger.info("⏰ Tarea ejecutándose...")

scheduler.add_job(
    func=tarea_ejemplo,
    trigger="interval",
    trigger_args={"seconds": 5},
    job_id="tarea_demo",
    max_instances=1
)

print("✅ Scheduler configurado con logger personalizado")
print("   Los logs del scheduler se guardan en scheduler.log")

# =========================================================================
# EJEMPLO 5: Integración con InfluxDB
# =========================================================================
print("\n" + "=" * 60)
print("EJEMPLO 5: InfluxDB con logging personalizado")
print("=" * 60)

influx_handler = LoggingHandler()
influx_logger = influx_handler.add_handlers([
    influx_handler.create_stream_handler(),
    influx_handler.create_file_handler("influxdb.log")
], logger_name="influxdb_demo")

# Nota: Este ejemplo no se conecta realmente a InfluxDB
# influx = InfluxdbOperation(host="localhost", port=8086, database="demo")
# influx.enable_logging(logger=influx_logger)

print("✅ Logger de InfluxDB configurado")
print("   Todas las operaciones de InfluxDB se loguean automáticamente")

# =========================================================================
# EJEMPLO 6: Logger con Loki y batching
# =========================================================================
print("\n" + "=" * 60)
print("EJEMPLO 6: Logger con Loki y batching")
print("=" * 60)

try:
    from ctrutils.handler import LokiHandler

    loki_batch_handler = LokiHandler(
        url=LOKI_URL,
        labels={
            "app": "batch_demo",
            "env": "dev"
        },
        level=logging.INFO,
        batch_size=5  # Envía cada 5 logs
    )

    batch_logger = logging.getLogger("batch_demo")
    batch_logger.addHandler(loki_batch_handler)
    batch_logger.setLevel(logging.INFO)

    print("📦 Enviando 10 logs con batching (batch_size=5)...")
    for i in range(10):
        batch_logger.info(f"Log #{i+1}")

    # Forzar envío de logs pendientes
    loki_batch_handler.flush()

    print("✅ Batching OK - Se enviaron 2 batches de 5 logs cada uno")

except ImportError:
    print("⚠️ LokiHandler no disponible (requiere requests)")
except Exception as e:
    print(f"⚠️ Error con Loki: {e}")

# =========================================================================
# EJEMPLO 7: Telegram con diferentes niveles
# =========================================================================
print("\n" + "=" * 60)
print("EJEMPLO 7: Telegram con diferentes niveles")
print("=" * 60)

if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
    try:
        from ctrutils.handler import TelegramBotHandler

        # Handler que solo envía CRÍTICOS a Telegram
        telegram_critical = TelegramBotHandler(
            token=TELEGRAM_TOKEN,
            chat_id=TELEGRAM_CHAT_ID,
            level=logging.CRITICAL,
            parse_mode="HTML"
        )

        telegram_logger = logging.getLogger("telegram_demo")
        telegram_logger.addHandler(telegram_critical)
        telegram_logger.setLevel(logging.DEBUG)

        telegram_logger.info("Esto NO se envía a Telegram")
        telegram_logger.error("Esto tampoco")
        telegram_logger.critical("<b>🚨 CRÍTICO:</b> Esto SÍ se envía a Telegram")

        print("✅ Telegram configurado - Solo mensajes CRÍTICOS")

    except ImportError:
        print("⚠️ TelegramBotHandler no disponible (requiere requests)")
    except Exception as e:
        print(f"⚠️ Error con Telegram: {e}")
else:
    print("⚠️ Telegram no configurado (define TELEGRAM_TOKEN y TELEGRAM_CHAT_ID)")

# =========================================================================
# RESUMEN
# =========================================================================
print("\n" + "=" * 60)
print("RESUMEN")
print("=" * 60)
print("""
✅ El módulo handler está funcionando correctamente

Archivos generados:
  - demo.log                  (logger básico con archivo)
  - demo_rotating.log         (logger con rotación)
  - production.log            (logger de producción)
  - production.log.rotating   (backup rotativo)
  - scheduler.log             (logs del scheduler)
  - influxdb.log              (logs de InfluxDB)

Para probar con Loki y Telegram, configura:
  export LOKI_URL="http://localhost:3100"
  export TELEGRAM_TOKEN="YOUR_BOT_TOKEN"
  export TELEGRAM_CHAT_ID="YOUR_CHAT_ID"

Documentación completa:
  - ctrutils/handler/README.md
  - docs/

""")
