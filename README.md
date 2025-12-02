# 🛠️ ctrutils

**ctrutils** es una librería minimalista de utilidades en Python enfocada en operaciones con InfluxDB, programación de tareas robusta (tipo Airflow), y logging centralizado.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 📦 Módulos

### ⏰ Scheduler
**Programación robusta de tareas tipo Airflow (mejorado en v11.0.0)**
- ✅ Ejecución continua que nunca termina (modo daemon)
- ✅ Dependencias entre tareas (DAGs - pipelines secuenciales)
- ✅ Reintentos automáticos con backoff exponencial
- ✅ Callbacks y hooks (on_success, on_failure, on_retry)
- ✅ Ejecución condicional
- ✅ Métricas detalladas
- ✅ Expresiones crontab completas
- ✅ Timeouts por tarea
- ✅ Graceful shutdown

[📖 Ver documentación completa del Scheduler](ctrutils/scheduler/README.md)

### 🗄️ InfluxDB Operations
**Operaciones avanzadas con InfluxDB**
- Validación automática de datos (NaN, infinitos, None)
- Escritura paralela para grandes volúmenes
- Downsampling y continuous queries
- Backup y restore de measurements
- Métricas de calidad de datos
- Métodos administrativos completos

### 📝 Handler (Logging & Notifications)
**Sistema de logging y notificaciones centralizado**
- **Logging**: Consola, archivos con rotación
- **Grafana Loki**: Logs centralizados y escalables
- **Telegram**: Notificaciones en tiempo real
- Integración completa con Scheduler e InfluxDB

## 🚀 Instalación

```bash
pip install ctrutils

# Para usar Loki y Telegram (opcional):
pip install requests
```

## 💡 Uso Rápido

### Scheduler - Nunca Termina

```python
from ctrutils.scheduler import Scheduler, Task

# Crear scheduler
scheduler = Scheduler(timezone="Europe/Madrid")

# Añadir tarea que se ejecuta cada 5 minutos
scheduler.add_job(
    func=mi_funcion,
    trigger="cron",
    job_id="tarea",
    trigger_args={"minute": "*/5"},
    max_retries=3,
)

# Iniciar (NUNCA termina hasta Ctrl+C)
scheduler.start(blocking=True)
```

### Scheduler - Pipeline ETL con Dependencias

```python
from ctrutils.scheduler import Scheduler, Task

scheduler = Scheduler()

# Extract
extract = Task(
    task_id="extract",
    func=extract_data,
    trigger_type="cron",
    trigger_args={"minute": "*/15"},
    max_retries=3,
)

# Transform (depende de Extract)
transform = Task(
    task_id="transform",
    func=transform_data,
    trigger_type="cron",
    trigger_args={"minute": "*/15"},
    dependencies=["extract"],  # Solo ejecuta si extract OK
    max_retries=3,
)

# Load (depende de Transform)
load = Task(
    task_id="load",
    func=load_data,
    trigger_type="cron",
    trigger_args={"minute": "*/15"},
    dependencies=["transform"],  # Solo ejecuta si transform OK
    on_failure=lambda e: alert_team(e),
)

scheduler.add_task(extract)
scheduler.add_task(transform)
scheduler.add_task(load)

# Nunca termina
scheduler.start(blocking=True)
```

### InfluxDB

```python
from ctrutils import InfluxdbOperation

influx = InfluxdbOperation(host='localhost', port=8086)

# Escribir DataFrame con validación automática
stats = influx.write_dataframe(
    measurement='datos',
    data=df,
    validate_data=True,  # Limpia NaN automáticamente
)

print(f"Escritos: {stats['successful_points']}")
```

### Logging

```python
from ctrutils.handler import LoggingHandler

# Crear logger con rotación
logger = LoggingHandler(
    logger_name="mi_app",
    level=logging.INFO,
)

# Añadir handlers
logger.add_handlers([
    logger.create_stream_handler(),
    logger.create_rotating_file_handler(
        filename="app.log",
        max_bytes=10*1024*1024,  # 10MB
        backup_count=5,
    )
])
```

## 📁 Estructura del Proyecto

```
ctrutils/
├── .coveragerc              # Coverage configuration
├── .isort.cfg               # Import sorting
├── .pylintrc                # Linting rules
├── mypy.ini                 # Type checking
├── pytest.ini               # Testing configuration
├── ctrutils/                # Código fuente principal
│   ├── database/           # Módulos de base de datos
│   │   └── influxdb/       # InfluxDB operations
│   ├── handler/            # Logging y notificaciones
│   │   ├── logging/        # Handlers de logging
│   │   └── notification/   # Loki, Telegram
│   └── scheduler/          # Scheduler robusto
├── docs/                    # Documentación
│   ├── scheduler/          # Docs específicas del scheduler
│   ├── PROJECT_STRUCTURE.md # Arquitectura del proyecto
│   ├── QUICK_START.md      # Guía rápida
│   └── TEST_SUMMARY.md     # Documentación de tests
├── examples/                # Ejemplos de uso
│   ├── scheduler_simple.py
│   └── scheduler_advanced_demo.py
├── tests/                   # Suite de tests
│   ├── unit/               # Tests unitarios
│   └── integration/        # Tests de integración
├── makefiles/              # Makefiles modulares
├── CHANGELOG.md            # Historial de cambios
├── README.md               # Este archivo
└── pyproject.toml          # Configuración del proyecto
```

## 🧪 Testing

El proyecto incluye una suite completa de tests:

```bash
# Ejecutar todos los tests
make test

# Solo tests unitarios (rápido, sin dependencias)
make test-unit

# Tests de integración (requiere InfluxDB)
make test-integration

# Tests con coverage
make test-coverage

# Ver todos los comandos disponibles
make help
```

## 📚 Documentación

- **[Quick Start](docs/QUICK_START.md)** - Guía de inicio rápido
- **[Project Structure](docs/PROJECT_STRUCTURE.md)** - Arquitectura y diseño del proyecto
- **[Scheduler Guide](ctrutils/scheduler/README.md)** - Documentación completa del scheduler
- **[Scheduler Cheat Sheet](docs/scheduler/SCHEDULER_CHEATSHEET.md)** - Referencia rápida
- **[Test Summary](docs/TEST_SUMMARY.md)** - Guía de testing
- **[Makefile Commands](makefiles/README.md)** - Comandos disponibles

## 🔧 Desarrollo

```bash
# Instalar dependencias de desarrollo
poetry install

# Ejecutar linters
make lint

# Formatear código
make format

# Verificar tipos
make type-check

# Verificación completa antes de commit
make check
```

## 📋 Requisitos

- Python 3.8+
- APScheduler 3.10+
- InfluxDB-Python 5.3+
- Pandas (para operaciones con DataFrames)

## 🤝 Contribución

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para guías de contribución.

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 🔗 Enlaces

- **Repositorio**: [GitHub](https://github.com/TacoronteRiveroCristian/ctrutils)
- **PyPI**: [ctrutils](https://pypi.org/project/ctrutils/)
- **Documentación**: [Docs](docs/)

## 📝 Changelog

Ver [CHANGELOG.md](CHANGELOG.md) para el historial completo de cambios.

## ⭐ Características Destacadas v11.0.0

### Scheduler Mejorado
El scheduler ha sido completamente refactorizado para ser una solución production-ready:

- **Nunca termina**: Modo daemon con `blocking=True`
- **DAGs completos**: Dependencias entre tareas tipo Airflow
- **Recuperación automática**: Reintentos con backoff exponencial
- **Monitoreo**: Métricas detalladas de ejecución
- **Robusto**: Thread-safe, graceful shutdown, timeouts

[Ver mejoras completas](docs/scheduler/SCHEDULER_IMPROVEMENTS.md)

---

**Desarrollado por**: Cristian Tacoronte Rivero  
**Versión**: 11.0.0
