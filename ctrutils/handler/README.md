# Handler Module 📝

Sistema centralizado de logging para **ctrutils** con soporte para múltiples outputs:
- 📺 **Consola** (StreamHandler)
- 📄 **Archivos** (FileHandler, RotatingFileHandler, TimedRotatingFileHandler)
- 🔍 **Grafana Loki** (LokiHandler) - Logs centralizados
- 💬 **Telegram** (TelegramBotHandler) - Notificaciones en tiempo real

---

## 🎯 Características

✅ **Centralizado**: Un solo punto de configuración para todos los logs
✅ **Flexible**: Múltiples handlers simultáneos (consola + archivo + Loki + Telegram)
✅ **Escalable**: Reutilizable en todos los módulos de ctrutils
✅ **Backward Compatible**: No rompe código existente (fallback a logging estándar)
✅ **Production Ready**: Rotación de archivos, timeouts, manejo de errores
✅ **Type Hints**: Completamente tipado para mejor DX

---

## 📦 Instalación

El handler está incluido en ctrutils. Para usar **Loki** y **Telegram**, instala:

```bash
pip install requests  # Requerido para LokiHandler y TelegramBotHandler
```

O con Poetry:

```bash
poetry add requests
```

---

## 🚀 Uso Básico

### Consola Simple

```python
from ctrutils.handler import LoggingHandler

# Método rápido
logger = LoggingHandler.quick_console_logger("myapp")
logger.info("¡Hola Mundo!")
```

### Archivo con Rotación

```python
from ctrutils.handler import LoggingHandler

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

logger.info("Este log va a consola Y archivo con rotación")
```

---

## 🔍 Grafana Loki (Logs Centralizados)

### Configuración Básica

```python
from ctrutils.handler import LoggingHandler

handler = LoggingHandler()
loki = handler.create_loki_handler(
    url="http://localhost:3100",
    labels={"app": "myapp", "env": "production"},
    level=logging.INFO
)

logger = handler.add_handlers([loki])
logger.info("Este log se envía a Loki automáticamente")
```

### Con Batching (Mejor Performance)

```python
from ctrutils.handler import LokiHandler
import logging

loki = LokiHandler(
    url="http://loki:3100",
    labels={
        "app": "data_processor",
        "env": "production",
        "host": "server-01",
        "version": "1.0.0"
    },
    level=logging.INFO,
    batch_size=10  # Envía cada 10 logs
)

logger = logging.getLogger("myapp")
logger.addHandler(loki)

# Al cerrar la app, enviar logs pendientes
import atexit
atexit.register(loki.flush)
```

### Consultas en Grafana

En Grafana Explorer (Loki):

```logql
{app="myapp", env="production"} |= "error"
```

```logql
{app="data_processor"} | json | level="ERROR"
```

---

## 💬 Telegram (Notificaciones)

### Configuración del Bot

1. Crear bot con [@BotFather](https://t.me/botfather):
   ```
   /newbot
   Nombre: MyApp Alerts Bot
   Username: myapp_alerts_bot
   ```

2. Obtener `TOKEN`: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`

3. Obtener `CHAT_ID`:
   ```bash
   # Envía un mensaje a tu bot, luego:
   curl https://api.telegram.org/bot<TOKEN>/getUpdates
   # Busca "chat":{"id":123456789}
   ```

### Uso Básico

```python
from ctrutils.handler import LoggingHandler
import logging

handler = LoggingHandler()
telegram = handler.create_telegram_handler(
    token="YOUR_BOT_TOKEN",
    chat_id="YOUR_CHAT_ID",
    level=logging.ERROR,  # Solo errores
    parse_mode="HTML"
)

logger = handler.add_handlers([telegram])

logger.info("Esto NO se envía a Telegram")
logger.error("❌ Esto SÍ se envía a Telegram")
```

### Con Formato HTML

```python
logger.error("<b>Error crítico:</b> <code>División por cero</code>")
logger.warning("<i>Advertencia:</i> Memoria al 90%")
```

---

## 🏭 Logger de Producción (All-in-One)

```python
from ctrutils.handler import LoggingHandler
import logging
import os

logger = LoggingHandler.production_logger(
    name="myapp",
    log_file="production.log",
    loki_url=os.getenv("LOKI_URL", "http://loki:3100"),
    loki_labels={
        "app": "myapp",
        "env": "production",
        "host": os.getenv("HOSTNAME", "unknown")
    },
    telegram_token=os.getenv("TELEGRAM_TOKEN"),
    telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
    level=logging.INFO
)

# Este logger:
# - Escribe a archivo production.log
# - Rota automáticamente (10MB, 5 backups)
# - Envía todos los logs a Loki
# - Envía solo ERRORS a Telegram

logger.info("App iniciada")  # → Archivo + Loki
logger.error("Error crítico!")  # → Archivo + Loki + Telegram 💬
```

---

## 🔧 Integración con Scheduler

```python
from ctrutils import Scheduler
from ctrutils.handler import LoggingHandler
import logging

# Configurar logger
logger = LoggingHandler.production_logger(
    name="scheduler",
    log_file="scheduler.log",
    loki_url="http://loki:3100",
    loki_labels={"app": "scheduler", "env": "prod"},
    telegram_token="YOUR_TOKEN",
    telegram_chat_id="YOUR_CHAT_ID"
)

# Pasar logger al Scheduler
scheduler = Scheduler(logger=logger)

def my_task():
    logger.info("Tarea ejecutándose...")
    # Si hay error, se loguea automáticamente

scheduler.add_job(
    my_task,
    trigger="interval",
    seconds=30,
    job_id="my_task"
)

scheduler.start()
```

---

## 🗄️ Integración con InfluxDB

```python
from ctrutils import InfluxdbOperation
from ctrutils.handler import LoggingHandler

# Configurar logger
handler = LoggingHandler()
logger = handler.add_handlers([
    handler.create_stream_handler(),
    handler.create_file_handler("influxdb.log"),
    handler.create_loki_handler(
        url="http://loki:3100",
        labels={"app": "influxdb", "env": "prod"}
    )
])

# Pasar logger a InfluxDB
influx = InfluxdbOperation(host="localhost", port=8086, database="mydb")
influx.enable_logging(logger=logger)

# Todas las operaciones logean automáticamente
influx.execute_query("SELECT * FROM measurement")
```

---

## 🛠️ API Reference

### LoggingHandler

#### Constructor

```python
LoggingHandler(
    level: int = logging.INFO,
    message_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    logger_name: Optional[str] = None
)
```

#### Métodos de Creación de Handlers

- `create_stream_handler()` → Consola
- `create_file_handler(log_file)` → Archivo plano
- `create_size_rotating_file_handler(log_file, max_bytes, backup_count)` → Rotación por tamaño
- `create_timed_rotating_file_handler(log_file, when, interval, backup_count)` → Rotación por tiempo
- `create_loki_handler(url, labels, level, timeout)` → Loki
- `create_telegram_handler(token, chat_id, level, parse_mode, timeout)` → Telegram

#### Métodos Estáticos (Quick Setup)

- `LoggingHandler.quick_console_logger(name, level)` → Logger consola
- `LoggingHandler.quick_file_logger(name, log_file, level)` → Logger consola + archivo
- `LoggingHandler.production_logger(...)` → Logger completo producción

#### Gestión de Handlers

- `add_handlers(handlers, logger_name)` → Agrega handlers al logger
- `remove_handlers(remove_all, handler_types)` → Elimina handlers

### LokiHandler

```python
LokiHandler(
    url: str,                    # "http://localhost:3100"
    labels: Dict[str, str],      # {"app": "myapp", "env": "prod"}
    level: int = logging.INFO,
    timeout: int = 5,
    batch_size: int = 0          # 0 = sin batching
)
```

**Métodos:**
- `flush()` → Envía logs pendientes (si batching está habilitado)
- `close()` → Cierra handler y envía logs pendientes

### TelegramBotHandler

```python
TelegramBotHandler(
    token: str,                          # Bot token de @BotFather
    chat_id: str,                        # Chat ID del destinatario
    level: int = logging.ERROR,          # Solo errores por defecto
    parse_mode: str = "HTML",            # "HTML", "Markdown", "MarkdownV2"
    timeout: int = 20
)
```

**Parse Modes:**
- `HTML`: `<b>bold</b>`, `<i>italic</i>`, `<code>code</code>`
- `Markdown`: `*bold*`, `_italic_`, `` `code` ``
- `MarkdownV2`: Markdown extendido

---

## 📊 Ejemplos Completos

### Ejemplo 1: Desarrollo Local

```python
from ctrutils.handler import LoggingHandler
import logging

logger = LoggingHandler.quick_console_logger("myapp", logging.DEBUG)

logger.debug("Debug info")
logger.info("App iniciada")
logger.warning("Advertencia")
logger.error("Error")
```

### Ejemplo 2: Producción con Loki

```python
from ctrutils.handler import LoggingHandler
import logging

handler = LoggingHandler(level=logging.INFO)
handlers_list = [
    handler.create_file_handler("production.log"),
    handler.create_loki_handler(
        url="http://loki:3100",
        labels={
            "app": "data_processor",
            "env": "production",
            "datacenter": "us-east-1"
        }
    )
]
logger = handler.add_handlers(handlers_list, logger_name="data_processor")

logger.info("Procesando 10000 registros...")
logger.info("Proceso completado exitosamente")
```

### Ejemplo 3: Alertas Críticas con Telegram

```python
from ctrutils.handler import LoggingHandler
import logging
import os

handler = LoggingHandler()

# Logger local (todos los niveles)
local_logger = handler.add_handlers([
    handler.create_stream_handler(),
    handler.create_file_handler("app.log")
], logger_name="app")

# Logger de alertas (solo críticos)
alert_handler = LoggingHandler(level=logging.CRITICAL)
alert_logger = alert_handler.add_handlers([
    alert_handler.create_telegram_handler(
        token=os.getenv("TELEGRAM_TOKEN"),
        chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        level=logging.CRITICAL
    )
], logger_name="alerts")

def process_critical_data():
    try:
        # Operación crítica
        result = perform_operation()
        local_logger.info(f"Operación exitosa: {result}")
    except Exception as e:
        local_logger.error(f"Error en operación: {e}")
        alert_logger.critical(f"🚨 <b>FALLO CRÍTICO:</b> {e}")
```

---

## 🧪 Testing

Para ejecutar los tests del handler:

```bash
# Todos los tests
make test

# Solo tests del handler
poetry run pytest tests/unit/handler/ -v

# Con coverage
poetry run pytest tests/unit/handler/ --cov=ctrutils.handler --cov-report=term
```

---

## 🐛 Troubleshooting

### "No se ha podido resolver la importación"

Asegúrate de que `requests` está instalado:

```bash
poetry add requests
```

### Loki no recibe logs

1. Verifica que Loki esté corriendo:
   ```bash
   curl http://localhost:3100/ready
   ```

2. Verifica la URL (debe incluir el esquema):
   ```python
   url="http://loki:3100"  # ✅ Correcto
   url="loki:3100"         # ❌ Incorrecto
   ```

3. Revisa logs de errores en stderr

### Telegram no envía mensajes

1. Verifica el token:
   ```bash
   curl https://api.telegram.org/bot<TOKEN>/getMe
   ```

2. Verifica el chat_id:
   ```bash
   curl https://api.telegram.org/bot<TOKEN>/getUpdates
   ```

3. Asegúrate de que el nivel de log es correcto:
   ```python
   level=logging.ERROR  # Solo errores
   level=logging.INFO   # Info y superiores
   ```

---

## 📚 Documentación Adicional

- [Documentación completa de ctrutils](../../README.md)
- [API Reference (Sphinx)](../../docs/)
- [Tests unitarios](../../tests/unit/handler/)
- [Tests de integración](../../tests/integration/handler/)

---

## 🤝 Contribuir

Para contribuir al handler module:

1. Fork el repositorio
2. Crea una rama: `git checkout -b feature/mi-feature`
3. Haz commit: `git commit -am 'Add feature'`
4. Push: `git push origin feature/mi-feature`
5. Crea un Pull Request

---

## 📝 Licencia

Este módulo es parte de **ctrutils** y está licenciado bajo [MIT License](../../LICENSE).

---

## 👨‍💻 Autor

Desarrollado por Cristian Taoronte Rivero

- GitHub: [@TacoronteRiveroCristian](https://github.com/TacoronteRiveroCristian)
- Proyecto: [ctrutils](https://github.com/TacoronteRiveroCristian/ctrutils)
