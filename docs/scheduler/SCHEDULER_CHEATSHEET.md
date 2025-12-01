# 📋 Scheduler - Cheat Sheet

## 🚀 Quick Start

```python
from ctrutils.scheduler import Scheduler, Task

# Crear scheduler
scheduler = Scheduler(timezone="Europe/Madrid", max_workers=10)

# Añadir tarea
scheduler.add_job(
    func=mi_funcion,
    trigger="cron",
    job_id="mi_tarea",
    trigger_args={"minute": "*/5"},  # Cada 5 minutos
)

# Iniciar (NUNCA termina)
scheduler.start(blocking=True)
```

## 📅 Expresiones Cron Comunes

```python
# Cada minuto
{"minute": "*"}

# Cada 5 minutos
{"minute": "*/5"}

# Cada hora (en punto)
{"hour": "*", "minute": 0}

# Cada 2 horas
{"hour": "*/2", "minute": 0}

# Cada día a las 9:00
{"hour": 9, "minute": 0}

# Lunes a viernes a las 9:00
{"day_of_week": "mon-fri", "hour": 9, "minute": 0}

# Primer día del mes a las 00:00
{"day": 1, "hour": 0, "minute": 0}

# Domingos a las 02:00
{"day_of_week": "sun", "hour": 2, "minute": 0}

# Cada 30 segundos (interval)
trigger="interval"
{"seconds": 30}
```

## 🔗 Dependencias (Secuenciales)

```python
# Task 1: Independiente
task1 = Task(
    task_id="extract",
    func=extract_data,
    trigger_type="cron",
    trigger_args={"minute": "*/15"},
)

# Task 2: Depende de task1
task2 = Task(
    task_id="transform",
    func=transform_data,
    trigger_type="cron",
    trigger_args={"minute": "*/15"},
    dependencies=["extract"],  # ← Solo ejecuta si 'extract' tuvo éxito
)

scheduler.add_task(task1)
scheduler.add_task(task2)
```

## ♻️ Reintentos

```python
task = Task(
    task_id="mi_tarea",
    func=funcion_que_puede_fallar,
    trigger_type="interval",
    trigger_args={"seconds": 60},
    max_retries=3,        # Reintentar hasta 3 veces
    retry_delay=60,       # 60s inicial
    retry_backoff=2.0,    # Exponencial: 60s, 120s, 240s
)
```

## 🎯 Callbacks

```python
def on_success(result):
    print(f"✓ Éxito: {result}")
    # Enviar notificación, actualizar BD, etc.

def on_failure(exception):
    print(f"✗ Fallo: {exception}")
    # Enviar alerta, rollback, etc.

def on_retry(exception, attempt):
    print(f"⟳ Reintento {attempt}: {exception}")

task = Task(
    ...,
    on_success=on_success,
    on_failure=on_failure,
    on_retry=on_retry,
)
```

## 🎭 Condicional

```python
def solo_horario_laboral():
    hour = datetime.now().hour
    return 9 <= hour < 18

task = Task(
    ...,
    condition=solo_horario_laboral,  # Solo ejecuta si retorna True
)
```

## ⏱️ Timeout

```python
task = Task(
    ...,
    timeout=30,  # Cancelar si tarda más de 30 segundos
)
```

## 📊 Métricas

```python
# Todas las métricas
metrics = scheduler.get_all_metrics()
print(f"Jobs ejecutados: {metrics['global']['total_jobs_executed']}")
print(f"Uptime: {metrics['global']['uptime_seconds']}s")

# Métricas de una tarea
task_metrics = scheduler.get_task_metrics("mi_tarea")
print(f"Tasa de éxito: {task_metrics['success_rate']:.1%}")
print(f"Duración promedio: {task_metrics['avg_duration']:.2f}s")
```

## 🎮 Control

```python
# Pausar
scheduler.pause_job("mi_tarea")

# Reanudar
scheduler.resume_job("mi_tarea")

# Re-programar
scheduler.reschedule_job("mi_tarea", "cron", hour=14, minute=0)

# Eliminar
scheduler.remove_job("mi_tarea")

# Listar
jobs = scheduler.get_jobs()
scheduler.print_jobs()

# Estado
if scheduler.is_running():
    print("Scheduler activo")

# Detener
scheduler.shutdown(wait=True)
```

## 🏗️ Configuración Avanzada

```python
scheduler = Scheduler(
    timezone="Europe/Madrid",
    max_workers=10,           # Máximo tareas concurrentes
    coalesce=True,            # Combinar ejecuciones perdidas
    misfire_grace_time=300,   # 5 min gracia para perdidas
)
```

## 📝 Método Simple vs Avanzado

### Simple (add_job)
```python
scheduler.add_job(
    func=mi_funcion,
    trigger="cron",
    job_id="tarea_simple",
    trigger_args={"minute": "*/5"},
    max_retries=2,
)
```

### Avanzado (Task)
```python
task = Task(
    task_id="tarea_avanzada",
    func=mi_funcion,
    trigger_type="cron",
    trigger_args={"minute": "*/5"},
    max_retries=3,
    retry_delay=60,
    retry_backoff=2.0,
    timeout=30,
    dependencies=["otra_tarea"],
    condition=lambda: es_hora(),
    on_success=callback_exito,
    on_failure=callback_fallo,
    on_retry=callback_retry,
)
scheduler.add_task(task)
```

## 🔥 Pipeline ETL Completo

```python
scheduler = Scheduler(timezone="Europe/Madrid", max_workers=5)

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
    dependencies=["extract"],
    max_retries=3,
)

# Load (depende de Transform)
load = Task(
    task_id="load",
    func=load_data,
    trigger_type="cron",
    trigger_args={"minute": "*/15"},
    dependencies=["transform"],
    max_retries=3,
    on_success=lambda r: notify("ETL OK"),
    on_failure=lambda e: alert(f"ETL FAIL: {e}"),
)

scheduler.add_task(extract)
scheduler.add_task(transform)
scheduler.add_task(load)

# Nunca termina
scheduler.start(blocking=True)
```

## ⚠️ Importante

1. **`blocking=True`** → Scheduler NUNCA termina (modo daemon)
2. **Dependencias** → La tarea solo se ejecuta si las dependencias tuvieron éxito
3. **Reintentos** → Backoff exponencial: delay × backoff^intento
4. **Thread-safe** → Todas las operaciones son seguras en multi-thread
5. **Graceful shutdown** → Ctrl+C o señales de sistema → cierre limpio

## 📚 Más Info

- `ctrutils/scheduler/README.md` - Documentación completa
- `examples/scheduler_simple.py` - Ejemplo básico
- `examples/scheduler_advanced_demo.py` - Ejemplo avanzado
- `SCHEDULER_RESUMEN.md` - Resumen completo de mejoras
