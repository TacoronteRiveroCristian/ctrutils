# Scheduler Module

Módulo avanzado de programación de tareas (scheduling) para Python, inspirado en Airflow pero más ligero y eficiente.

## 🚀 Características Principales

- **🔄 Ejecución Continua**: Modo daemon que nunca termina (ideal para servicios)
- **🔗 Dependencias**: Tareas secuenciales y condicionales con DAG (Directed Acyclic Graph)
- **♻️ Reintentos Automáticos**: Con backoff exponencial configurable
- **🎯 Callbacks & Hooks**: `on_success`, `on_failure`, `on_retry`
- **📊 Monitoreo**: Métricas detalladas de ejecución y rendimiento
- **⚡ Gestión Robusta**: Manejo de errores, timeouts, señales de sistema
- **📅 Cron Expressions**: Soporte completo para expresiones crontab
- **🎭 Ejecución Condicional**: Tareas que se ejecutan solo si se cumple una condición
- **⏱️ Timeouts**: Control de tiempo máximo de ejecución por tarea
- **🔄 Shutdown Graceful**: Cierre controlado con señales SIGINT/SIGTERM

## 📦 Instalación

```bash
pip install ctrutils
```

## 🎯 Uso Básico

### Ejemplo Simple

```python
from ctrutils.scheduler import Scheduler
from datetime import datetime

# Crear scheduler
scheduler = Scheduler(timezone="Europe/Madrid")

# Añadir tarea que se ejecuta cada minuto
scheduler.add_job(
    func=lambda: print(f"[{datetime.now()}] Tarea ejecutada!"),
    trigger="interval",
    job_id="simple_task",
    trigger_args={"seconds": 60},
)

# Iniciar (modo blocking - nunca termina)
scheduler.start(blocking=True)
```

### Ejemplo con Reintentos y Callbacks

```python
from ctrutils.scheduler import Scheduler

def tarea_critica():
    # Simulación de tarea que puede fallar
    import random
    if random.random() < 0.3:
        raise Exception("Error temporal")
    return "Éxito"

def on_success(result):
    print(f"✓ Tarea completada: {result}")

def on_failure(exception):
    print(f"✗ Tarea falló permanentemente: {exception}")
    # Enviar alerta, notificación, etc.

def on_retry(exception, attempt):
    print(f"⟳ Reintentando (intento {attempt}): {exception}")

scheduler = Scheduler()

scheduler.add_job(
    func=tarea_critica,
    trigger="cron",
    job_id="critical_task",
    trigger_args={"hour": "*/2", "minute": 0},  # Cada 2 horas
    max_retries=3,
    retry_delay=60,  # 60s, 120s, 240s (backoff exponencial)
    on_success=on_success,
    on_failure=on_failure,
    on_retry=on_retry,
)

scheduler.start(blocking=True)
```

## 🔗 Pipeline ETL con Dependencias

Ideal para pipelines de datos tipo Airflow:

```python
from ctrutils.scheduler import Scheduler, Task

def extract_data():
    print("Extrayendo datos...")
    # Tu lógica aquí
    return {"records": 1000}

def transform_data():
    print("Transformando datos...")
    # Tu lógica aquí
    return {"transformed": 1000}

def load_data():
    print("Cargando datos...")
    # Tu lógica aquí
    return {"loaded": 1000}

scheduler = Scheduler(max_workers=5)

# Task 1: Extract (independiente)
extract_task = Task(
    task_id="extract",
    func=extract_data,
    trigger_type="cron",
    trigger_args={"minute": "*/15"},  # Cada 15 minutos
    max_retries=3,
    retry_delay=30,
)

# Task 2: Transform (depende de Extract)
transform_task = Task(
    task_id="transform",
    func=transform_data,
    trigger_type="cron",
    trigger_args={"minute": "*/15"},
    dependencies=["extract"],  # Solo se ejecuta si extract tuvo éxito
    max_retries=3,
)

# Task 3: Load (depende de Transform)
load_task = Task(
    task_id="load",
    func=load_data,
    trigger_type="cron",
    trigger_args={"minute": "*/15"},
    dependencies=["transform"],  # Solo se ejecuta si transform tuvo éxito
    max_retries=3,
)

# Añadir tareas al scheduler
scheduler.add_task(extract_task)
scheduler.add_task(transform_task)
scheduler.add_task(load_task)

# Iniciar pipeline
scheduler.start(blocking=True)
```

## 🎭 Ejecución Condicional

```python
from ctrutils.scheduler import Scheduler, Task
from datetime import datetime

def is_business_hours():
    """Condición: solo ejecutar en horario laboral."""
    hour = datetime.now().hour
    return 9 <= hour < 18

def business_task():
    print("Ejecutando tarea de negocio...")

scheduler = Scheduler()

task = Task(
    task_id="business_only",
    func=business_task,
    trigger_type="cron",
    trigger_args={"minute": "*/30"},  # Cada 30 minutos
    condition=is_business_hours,  # Solo se ejecuta si retorna True
)

scheduler.add_task(task)
scheduler.start(blocking=True)
```

## ⏱️ Timeouts y Control de Ejecución

```python
from ctrutils.scheduler import Scheduler, Task

def long_running_task():
    import time
    time.sleep(100)  # Simula tarea larga

scheduler = Scheduler()

task = Task(
    task_id="timeout_task",
    func=long_running_task,
    trigger_type="interval",
    trigger_args={"seconds": 60},
    timeout=30,  # Se cancela si excede 30 segundos
    max_retries=2,
)

scheduler.add_task(task)
scheduler.start(blocking=True)
```

## 📊 Monitoreo y Métricas

```python
from ctrutils.scheduler import Scheduler
import time

scheduler = Scheduler()

# Añadir tareas...
scheduler.add_job(
    func=lambda: time.sleep(1),
    trigger="interval",
    job_id="task1",
    trigger_args={"seconds": 10},
)

scheduler.start()

# Obtener métricas globales
while True:
    time.sleep(30)
    metrics = scheduler.get_all_metrics()

    print(f"Uptime: {metrics['global']['uptime_seconds']}s")
    print(f"Jobs ejecutados: {metrics['global']['total_jobs_executed']}")
    print(f"Fallos: {metrics['global']['total_failures']}")

    # Métricas por tarea
    for task_id, task_metrics in metrics['tasks'].items():
        print(f"\nTarea: {task_id}")
        print(f"  - Ejecuciones: {task_metrics['total_runs']}")
        print(f"  - Tasa de éxito: {task_metrics['success_rate']:.2%}")
        print(f"  - Duración promedio: {task_metrics['avg_duration']:.2f}s")

# Métricas de una tarea específica
task_metrics = scheduler.get_task_metrics("task1")
print(task_metrics)
```

## 📅 Expresiones Cron

Soporte completo para expresiones crontab:

```python
# Cada hora
trigger_args={"hour": "*", "minute": 0}

# Cada 15 minutos
trigger_args={"minute": "*/15"}

# De lunes a viernes a las 9:00
trigger_args={"day_of_week": "mon-fri", "hour": 9, "minute": 0}

# Primer día del mes a las 00:00
trigger_args={"day": 1, "hour": 0, "minute": 0}

# Cada domingo a las 02:00
trigger_args={"day_of_week": "sun", "hour": 2, "minute": 0}

# Específico: 10:30 y 14:30 todos los días
trigger_args={"hour": "10,14", "minute": 30}
```

## 🔄 Gestión Avanzada

### Pausar/Reanudar Tareas

```python
# Pausar una tarea
scheduler.pause_job("task_id")

# Reanudar una tarea
scheduler.resume_job("task_id")
```

### Re-programar Tareas

```python
# Cambiar el schedule de una tarea existente
scheduler.reschedule_job(
    "task_id",
    "cron",
    hour=12,
    minute=0,
)
```

### Eliminar Tareas

```python
# Eliminar una tarea
scheduler.remove_job("task_id")
```

### Ver Tareas Programadas

```python
# Listar todas las tareas
jobs = scheduler.get_jobs()
for job in jobs:
    print(f"ID: {job.id}, Próxima ejecución: {job.next_run_time}")

# Imprimir información detallada
scheduler.print_jobs()
```

## 🛡️ Shutdown Graceful

El scheduler maneja automáticamente las señales SIGINT y SIGTERM:

```python
scheduler = Scheduler()

# Añadir tareas...

# Cuando se reciba Ctrl+C o señal de terminación:
# - Se detiene la aceptación de nuevas tareas
# - Se espera a que terminen las tareas en ejecución
# - Se cierra limpiamente
scheduler.start(blocking=True)
```

## ⚙️ Configuración Avanzada

```python
scheduler = Scheduler(
    timezone="Europe/Madrid",
    max_workers=10,  # Máximo de tareas concurrentes
    coalesce=True,  # Combinar ejecuciones perdidas
    misfire_grace_time=300,  # 5 min de gracia para ejecuciones perdidas
)
```

## 🎯 Casos de Uso

### 1. ETL Pipeline
Pipeline de extracción, transformación y carga de datos con dependencias.

### 2. Monitoreo Continuo
Health checks, verificación de servicios, alertas.

### 3. Tareas Programadas
Backups, limpieza de archivos temporales, reportes diarios.

### 4. Procesamiento por Lotes
Procesar archivos, sincronizar datos, actualizar cachés.

### 5. Notificaciones
Envío programado de emails, notificaciones push, reportes.

## 📝 API Reference

### Scheduler

**Constructor:**
```python
Scheduler(
    logger: Optional[logging.Logger] = None,
    timezone: str = "UTC",
    max_workers: int = 10,
    coalesce: bool = True,
    misfire_grace_time: int = 300,
)
```

**Métodos principales:**
- `add_job(...)`: Añadir tarea (método simplificado)
- `add_task(task: Task)`: Añadir tarea (método avanzado)
- `remove_job(job_id: str)`: Eliminar tarea
- `start(blocking: bool = False)`: Iniciar scheduler
- `shutdown(wait: bool = True)`: Detener scheduler
- `pause_job(job_id: str)`: Pausar tarea
- `resume_job(job_id: str)`: Reanudar tarea
- `reschedule_job(job_id: str, ...)`: Re-programar tarea
- `get_jobs()`: Lista de tareas
- `get_task_metrics(task_id: str)`: Métricas de una tarea
- `get_all_metrics()`: Todas las métricas
- `is_running()`: Estado del scheduler
- `print_jobs()`: Imprimir información de tareas

### Task

**Constructor:**
```python
Task(
    task_id: str,
    func: Callable,
    trigger_type: str,  # 'cron', 'interval', 'date'
    trigger_args: Dict[str, Any],
    max_retries: int = 3,
    retry_delay: int = 60,
    retry_backoff: float = 2.0,
    timeout: Optional[int] = None,
    dependencies: Optional[List[str]] = None,
    on_success: Optional[Callable] = None,
    on_failure: Optional[Callable] = None,
    on_retry: Optional[Callable] = None,
    condition: Optional[Callable[[], bool]] = None,
    args: Optional[tuple] = None,
    kwargs: Optional[Dict[str, Any]] = None,
)
```

### JobState (Enum)

- `PENDING`: Tarea pendiente
- `RUNNING`: En ejecución
- `SUCCESS`: Completada exitosamente
- `FAILED`: Falló permanentemente
- `RETRYING`: En reintento
- `SKIPPED`: Omitida (por condición o dependencias)

### JobMetrics

**Propiedades:**
- `total_runs`: Total de ejecuciones
- `successes`: Ejecuciones exitosas
- `failures`: Fallos
- `retries`: Reintentos
- `success_rate`: Tasa de éxito
- `avg_duration`: Duración promedio
- `last_run_time`: Última ejecución
- `last_duration`: Duración de última ejecución
- `last_state`: Último estado

## 🤝 Comparación con Airflow

| Característica | ctrutils.scheduler | Airflow |
|----------------|-------------------|---------|
| Instalación | Ligera (~1 MB) | Pesada (~100 MB+) |
| Configuración | Simple, código Python | Compleja, archivos config |
| DAGs | Soportado (dependencias) | Soportado |
| UI Web | ❌ | ✅ |
| Reintentos | ✅ | ✅ |
| Callbacks | ✅ | ✅ |
| Métricas | ✅ (programáticas) | ✅ (UI) |
| Uso de recursos | Bajo | Alto |
| Curva de aprendizaje | Baja | Alta |

**Cuándo usar ctrutils.scheduler:**
- Proyectos pequeños/medianos
- Necesitas algo ligero y eficiente
- No necesitas UI web
- Quieres control total desde código

**Cuándo usar Airflow:**
- Proyectos grandes/enterprise
- Múltiples equipos
- Necesitas UI web
- Auditoría y compliance estrictos

## 📄 Licencia

Ver archivo LICENSE del proyecto.

## 🔗 Enlaces

- [Documentación completa](../README.md)
- [Ejemplos](../examples/)
- [Tests](../tests/unit/test_scheduler.py)
