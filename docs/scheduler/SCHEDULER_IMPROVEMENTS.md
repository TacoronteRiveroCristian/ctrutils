# 🚀 Mejoras del Módulo Scheduler - Versión 11.0.0

## 📋 Resumen Ejecutivo

Se ha realizado una **refactorización completa** del módulo `scheduler` para convertirlo en una solución robusta, eficiente y tipo "mini-Airflow" para la programación y gestión de tareas en Python.

## ✨ Nuevas Características

### 1. 🔄 Ejecución Continua (Daemon Mode)
- **Antes**: El scheduler se iniciaba en background pero requería mantener el proceso principal activo
- **Ahora**: Modo `blocking=True` que mantiene el scheduler ejecutándose indefinidamente
```python
scheduler.start(blocking=True)  # Nunca termina hasta Ctrl+C o señal
```

### 2. 🔗 Dependencias y DAGs (Directed Acyclic Graph)
- **Nueva clase `Task`** con soporte para dependencias
- **Ejecución secuencial** garantizada: una tarea solo se ejecuta si sus dependencias tuvieron éxito
- **Ideal para pipelines** ETL, procesamiento de datos, workflows

```python
# Task que depende de otra
transform_task = Task(
    task_id="transform",
    func=transform_data,
    dependencies=["extract"],  # Solo ejecuta si 'extract' tuvo éxito
    ...
)
```

### 3. ♻️ Reintentos Automáticos con Backoff Exponencial
- **Reintentos configurables**: `max_retries`, `retry_delay`, `retry_backoff`
- **Backoff exponencial**: delay × backoff^intento
- **Tracking de reintentos**: métricas detalladas

```python
task = Task(
    max_retries=3,
    retry_delay=60,  # 60s, 120s, 240s
    retry_backoff=2.0,  # Exponencial
    ...
)
```

### 4. 🎯 Callbacks y Hooks
- **on_success**: Se ejecuta cuando la tarea tiene éxito
- **on_failure**: Se ejecuta cuando falla permanentemente (después de todos los reintentos)
- **on_retry**: Se ejecuta en cada reintento

```python
task = Task(
    on_success=lambda r: send_notification("Success!"),
    on_failure=lambda e: alert_team(f"Critical failure: {e}"),
    on_retry=lambda e, n: log_retry(e, n),
    ...
)
```

### 5. 📊 Sistema de Métricas Completo
- **Métricas globales**: total de ejecuciones, fallos, reintentos, uptime
- **Métricas por tarea**: éxitos, fallos, tasa de éxito, duración promedio
- **Nueva clase `JobMetrics`** para tracking detallado
- **Nuevos estados**: `JobState` enum (PENDING, RUNNING, SUCCESS, FAILED, RETRYING, SKIPPED)

```python
metrics = scheduler.get_all_metrics()
# {
#   "global": {
#     "total_jobs_executed": 150,
#     "total_failures": 5,
#     "uptime_seconds": 3600,
#     ...
#   },
#   "tasks": {
#     "task1": {
#       "total_runs": 50,
#       "success_rate": 0.96,
#       "avg_duration": 1.5,
#       ...
#     }
#   }
# }
```

### 6. 🎭 Ejecución Condicional
- **Condiciones dinámicas**: tareas que se ejecutan solo si se cumple una función
- **Uso casos**: horario laboral, disponibilidad de recursos, etc.

```python
task = Task(
    condition=lambda: datetime.now().hour >= 9 and datetime.now().hour < 18,
    ...  # Solo ejecuta en horario laboral
)
```

### 7. ⏱️ Timeouts de Ejecución
- **Control de tiempo**: limite máximo de ejecución por tarea
- **Prevención de bloqueos**: tareas que tardan demasiado se cancelan automáticamente

```python
task = Task(
    timeout=30,  # Máximo 30 segundos
    ...
)
```

### 8. 🛡️ Shutdown Graceful
- **Manejo de señales**: SIGINT (Ctrl+C) y SIGTERM
- **Cierre controlado**: espera a que terminen las tareas en ejecución
- **Sin pérdida de datos**: shutdown limpio y seguro

```python
# Automático con blocking=True
scheduler.start(blocking=True)

# O manual con wait
scheduler.shutdown(wait=True)
```

### 9. ⚙️ Control Avanzado de Tareas
- **Pausar/Reanudar**: `pause_job()`, `resume_job()`
- **Re-programar**: `reschedule_job()` cambiar el schedule dinámicamente
- **Eliminar**: `remove_job()` con limpieza completa
- **Consultar**: `get_jobs()`, `print_jobs()`, `is_running()`

### 10. 🎯 Configuración Robusta
- **Max workers**: control de concurrencia
- **Coalesce**: combinar ejecuciones perdidas
- **Misfire grace time**: tiempo de gracia para ejecuciones perdidas
- **Timezone**: soporte completo de zonas horarias

```python
scheduler = Scheduler(
    max_workers=10,
    coalesce=True,
    misfire_grace_time=300,
    timezone="Europe/Madrid",
)
```

## 🏗️ Arquitectura Mejorada

### Clases Principales

#### 1. `Scheduler`
- Orquestador principal
- Gestión de tareas y recursos
- Monitoreo de métricas
- Manejo de eventos y señales

#### 2. `Task`
- Encapsulación completa de una tarea
- Configuración de dependencias, reintentos, callbacks
- Estado y métricas propias

#### 3. `JobState` (Enum)
- Estados bien definidos: PENDING, RUNNING, SUCCESS, FAILED, RETRYING, SKIPPED
- Tracking preciso del ciclo de vida

#### 4. `JobMetrics`
- Métricas detalladas por tarea
- Historial de ejecuciones
- Cálculos automáticos (avg_duration, success_rate, etc.)

### Thread Safety
- **Threading.RLock**: operaciones thread-safe en estructuras compartidas
- **Event coordinación**: shutdown coordinado entre threads
- **APScheduler**: manejo interno de thread pool

## 📝 Cambios en la API

### Métodos Nuevos

```python
# Scheduler
scheduler.add_task(task: Task)  # Método avanzado
scheduler.get_task_metrics(task_id: str)  # Métricas de una tarea
scheduler.get_all_metrics()  # Todas las métricas
scheduler.is_running()  # Estado del scheduler
scheduler.pause_job(job_id: str)  # Pausar
scheduler.resume_job(job_id: str)  # Reanudar
scheduler.reschedule_job(job_id: str, ...)  # Re-programar
scheduler.print_jobs()  # Imprimir información
```

### Métodos Actualizados

```python
# add_job ahora soporta:
scheduler.add_job(
    ...,
    max_retries=3,  # NUEVO
    retry_delay=60,  # NUEVO
    dependencies=["task1"],  # NUEVO
    on_success=callback,  # NUEVO
    on_failure=callback,  # NUEVO
)

# start ahora soporta:
scheduler.start(blocking=True)  # NUEVO: modo daemon

# shutdown ahora soporta:
scheduler.shutdown(wait=True)  # NUEVO: esperar a tareas
```

### Compatibilidad hacia atrás
✅ **100% compatible** con el código existente. Los métodos antiguos siguen funcionando:
- `add_job()` con parámetros básicos
- `start()` sin blocking
- `shutdown()` sin wait
- `get_jobs()`, `remove_job()`

## 📦 Archivos Modificados/Creados

### Modificados
1. **`ctrutils/scheduler/scheduler.py`** (149 → 751 líneas)
   - Refactorización completa
   - Nuevas clases: Task, JobState, JobMetrics
   - Nuevos métodos y funcionalidades

2. **`tests/unit/test_scheduler.py`** (133 → 359 líneas)
   - Tests para nuevas funcionalidades
   - Tests de JobMetrics, Task
   - Tests de callbacks, reintentos, dependencias

3. **`ctrutils/scheduler/__init__.py`**
   - Exportar Task, JobState, JobMetrics

### Creados
1. **`ctrutils/scheduler/README.md`**
   - Documentación completa del módulo
   - Ejemplos de uso
   - API reference
   - Comparación con Airflow

2. **`examples/scheduler_advanced_demo.py`**
   - Ejemplo completo de pipeline ETL
   - Dependencias secuenciales
   - Tareas condicionales
   - Monitoreo de métricas
   - Uso de callbacks

3. **`tests/test_scheduler_quick.py`**
   - Test rápido de funcionalidades
   - Verificación de métricas
   - Pruebas de integración

## 🎯 Casos de Uso Principales

### 1. Pipeline ETL
```python
# Extract → Transform → Load con dependencias
extract_task → transform_task → load_task
```

### 2. Tareas Programadas
```python
# Backups diarios, limpiezas, reportes
scheduler.add_job(..., trigger="cron", trigger_args={"hour": 2})
```

### 3. Monitoreo Continuo
```python
# Health checks, verificaciones periódicas
scheduler.add_job(..., trigger="interval", trigger_args={"seconds": 30})
```

### 4. Procesamiento con Reintentos
```python
# APIs externas, servicios inestables
task = Task(..., max_retries=5, retry_backoff=2.0)
```

### 5. Workflows Condicionales
```python
# Solo en horario laboral, solo si hay datos, etc.
task = Task(..., condition=lambda: check_condition())
```

## 📊 Mejoras de Rendimiento

- **Thread pool configurable**: mejor uso de recursos con `max_workers`
- **Coalesce**: evita ejecuciones múltiples innecesarias
- **Misfire grace time**: manejo inteligente de ejecuciones perdidas
- **Lazy loading**: carga de dependencias solo cuando se necesitan

## 🔒 Seguridad y Robustez

- **Thread-safe**: operaciones seguras en entornos multi-thread
- **Exception handling**: captura y manejo de todos los errores
- **Signal handling**: shutdown graceful con SIGINT/SIGTERM
- **Logging completo**: trazabilidad de todas las operaciones
- **Timeout protection**: prevención de tareas colgadas

## 🧪 Cobertura de Tests

Nueva suite de tests que cubre:
- ✅ Creación y gestión de tareas
- ✅ Dependencias entre tareas
- ✅ Reintentos automáticos
- ✅ Callbacks (success, failure, retry)
- ✅ Métricas (globales y por tarea)
- ✅ Control de scheduler (pause, resume, reschedule)
- ✅ Ejecución condicional
- ✅ Estados de tareas

## 🚦 Migración desde Versión Anterior

### Código Antiguo (sigue funcionando)
```python
scheduler = Scheduler()
scheduler.add_job(
    func=my_function,
    trigger="interval",
    job_id="my_job",
    trigger_args={"seconds": 60}
)
scheduler.start()
```

### Código Nuevo (aprovecha nuevas funcionalidades)
```python
scheduler = Scheduler(max_workers=5)

task = Task(
    task_id="my_task",
    func=my_function,
    trigger_type="interval",
    trigger_args={"seconds": 60},
    max_retries=3,
    on_success=lambda r: print(f"Success: {r}"),
    on_failure=lambda e: alert(f"Failed: {e}"),
)
scheduler.add_task(task)
scheduler.start(blocking=True)  # Nunca termina
```

## 📚 Documentación

- **README.md**: `/ctrutils/scheduler/README.md` (completo)
- **Ejemplos**: `/examples/scheduler_advanced_demo.py` (350+ líneas)
- **Tests**: `/tests/unit/test_scheduler.py` (359 líneas)
- **Quick test**: `/tests/test_scheduler_quick.py` (200+ líneas)

## 🎯 Comparación con Airflow

| Característica | ctrutils.scheduler | Airflow |
|----------------|-------------------|---------|
| **Instalación** | Ligera (~1 MB) | Pesada (~100+ MB) |
| **Setup** | 5 líneas código | Config compleja |
| **DAGs** | ✅ (dependencias) | ✅ |
| **Reintentos** | ✅ | ✅ |
| **Callbacks** | ✅ | ✅ |
| **UI Web** | ❌ | ✅ |
| **Métricas** | ✅ (código) | ✅ (UI) |
| **Recursos** | Bajo | Alto |
| **Curva aprendizaje** | Baja | Alta |

## ✅ Conclusión

El módulo `scheduler` ahora es una solución **production-ready** para:
- ✅ Ejecutarse **indefinidamente** sin intervención
- ✅ Manejar **pipelines complejos** con dependencias
- ✅ **Recuperarse automáticamente** de fallos temporales
- ✅ Proporcionar **visibilidad completa** con métricas
- ✅ Ser **ligero y eficiente** para cualquier proyecto

**Es como tener Airflow pero sin la complejidad y overhead.**

## 🚀 Próximos Pasos

Para usar el nuevo scheduler:

1. **Instalar dependencias** (si no están):
   ```bash
   pip install apscheduler
   ```

2. **Ver ejemplos**:
   ```bash
   python examples/scheduler_advanced_demo.py
   ```

3. **Ejecutar tests**:
   ```bash
   python -m pytest tests/unit/test_scheduler.py -v
   # o
   python tests/test_scheduler_quick.py
   ```

4. **Leer documentación**:
   - `ctrutils/scheduler/README.md`

---

**Versión**: 11.0.0
**Fecha**: Noviembre 2025
**Autor**: Cristian Tacoronte Rivero
