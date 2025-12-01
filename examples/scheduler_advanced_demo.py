"""
Ejemplo avanzado de uso del Scheduler con dependencias, reintentos y callbacks.

Este ejemplo demuestra:
- Tareas con dependencias secuenciales
- Tareas condicionales
- Reintentos automáticos con backoff exponencial
- Callbacks (on_success, on_failure, on_retry)
- Ejecución continua tipo daemon
- Monitoreo de métricas
"""

import time
import random
from datetime import datetime

from ctrutils.scheduler import Scheduler, Task


def extract_data():
    """Simula extracción de datos."""
    print(f"[{datetime.now()}] Extracting data...")
    time.sleep(2)

    # Simula fallo ocasional
    if random.random() < 0.2:
        raise Exception("Failed to extract data from source")

    print(f"[{datetime.now()}] Data extraction completed!")
    return {"records": 1000}


def transform_data():
    """Simula transformación de datos."""
    print(f"[{datetime.now()}] Transforming data...")
    time.sleep(1.5)

    # Simula fallo ocasional
    if random.random() < 0.15:
        raise Exception("Transformation error")

    print(f"[{datetime.now()}] Data transformation completed!")
    return {"transformed": 1000}


def load_data():
    """Simula carga de datos."""
    print(f"[{datetime.now()}] Loading data to destination...")
    time.sleep(1)

    # Simula fallo ocasional
    if random.random() < 0.1:
        raise Exception("Failed to load data")

    print(f"[{datetime.now()}] Data load completed!")
    return {"loaded": 1000}


def send_notification(result=None):
    """Simula envío de notificación."""
    print(f"[{datetime.now()}] Sending notification...")
    time.sleep(0.5)
    print(f"[{datetime.now()}] Notification sent!")


def cleanup_temp_files():
    """Limpia archivos temporales."""
    print(f"[{datetime.now()}] Cleaning up temporary files...")
    time.sleep(0.5)
    print(f"[{datetime.now()}] Cleanup completed!")


def health_check():
    """Verifica el estado del sistema."""
    print(f"[{datetime.now()}] Running health check...")
    # Simula chequeo de salud
    is_healthy = random.random() > 0.05
    print(f"[{datetime.now()}] System is {'healthy' if is_healthy else 'unhealthy'}!")
    return is_healthy


def on_task_success(result):
    """Callback ejecutado cuando una tarea tiene éxito."""
    print(f"✓ Task succeeded with result: {result}")


def on_task_failure(exception):
    """Callback ejecutado cuando una tarea falla definitivamente."""
    print(f"✗ Task failed permanently: {exception}")
    # Aquí podrías enviar alertas, notificaciones, etc.


def on_task_retry(exception, attempt):
    """Callback ejecutado en cada reintento."""
    print(f"⟳ Retrying task (attempt {attempt}): {exception}")


def business_hours_condition():
    """Condición: solo ejecutar en horario laboral (9-18h)."""
    current_hour = datetime.now().hour
    return 9 <= current_hour < 18


def main():
    """Ejemplo principal del scheduler avanzado."""
    print("=" * 80)
    print("ADVANCED SCHEDULER DEMO - Type Airflow")
    print("=" * 80)
    print()

    # Crear scheduler con configuración robusta
    scheduler = Scheduler(
        timezone="Europe/Madrid",
        max_workers=5,  # Máximo 5 tareas concurrentes
        coalesce=True,  # Combina ejecuciones perdidas
        misfire_grace_time=300,  # 5 minutos de gracia para ejecuciones perdidas
    )

    # =========================================================================
    # PIPELINE ETL CON DEPENDENCIAS SECUENCIALES
    # =========================================================================
    print("📋 Setting up ETL pipeline with dependencies...")

    # Task 1: Extract (se ejecuta cada 5 minutos)
    extract_task = Task(
        task_id="extract_data",
        func=extract_data,
        trigger_type="cron",
        trigger_args={"minute": "*/5"},  # Cada 5 minutos
        max_retries=3,
        retry_delay=30,  # 30 segundos inicial
        retry_backoff=2.0,  # Backoff exponencial: 30s, 60s, 120s
        timeout=30,
        on_success=on_task_success,
        on_failure=on_task_failure,
        on_retry=on_task_retry,
    )

    # Task 2: Transform (depende de Extract)
    transform_task = Task(
        task_id="transform_data",
        func=transform_data,
        trigger_type="cron",
        trigger_args={"minute": "*/5"},
        max_retries=3,
        retry_delay=20,
        retry_backoff=2.0,
        dependencies=["extract_data"],  # Solo se ejecuta si extract_data tuvo éxito
        on_success=on_task_success,
        on_failure=on_task_failure,
        on_retry=on_task_retry,
    )

    # Task 3: Load (depende de Transform)
    load_task = Task(
        task_id="load_data",
        func=load_data,
        trigger_type="cron",
        trigger_args={"minute": "*/5"},
        max_retries=3,
        retry_delay=20,
        retry_backoff=2.0,
        dependencies=["transform_data"],  # Solo se ejecuta si transform_data tuvo éxito
        on_success=on_task_success,
        on_failure=on_task_failure,
        on_retry=on_task_retry,
    )

    # Task 4: Notification (depende de Load)
    notification_task = Task(
        task_id="send_notification",
        func=send_notification,
        trigger_type="cron",
        trigger_args={"minute": "*/5"},
        max_retries=2,
        retry_delay=10,
        dependencies=["load_data"],
        on_success=lambda r: print("✉ Notification sent successfully!"),
    )

    # Task 5: Cleanup (se ejecuta siempre después del pipeline)
    cleanup_task = Task(
        task_id="cleanup_temp_files",
        func=cleanup_temp_files,
        trigger_type="cron",
        trigger_args={"minute": "*/5"},
        max_retries=1,
        dependencies=["send_notification"],
    )

    # Añadir tareas del pipeline ETL
    scheduler.add_task(extract_task)
    scheduler.add_task(transform_task)
    scheduler.add_task(load_task)
    scheduler.add_task(notification_task)
    scheduler.add_task(cleanup_task)

    # =========================================================================
    # TAREAS ADICIONALES
    # =========================================================================
    print("📋 Setting up additional tasks...")

    # Health check cada 30 segundos
    health_check_task = Task(
        task_id="health_check",
        func=health_check,
        trigger_type="interval",
        trigger_args={"seconds": 30},
        max_retries=0,  # No reintentar health checks
    )
    scheduler.add_task(health_check_task)

    # Tarea condicional: solo en horario laboral (cada minuto)
    business_hours_task = Task(
        task_id="business_hours_task",
        func=lambda: print(f"[{datetime.now()}] Business hours task executed!"),
        trigger_type="cron",
        trigger_args={"minute": "*"},  # Cada minuto
        condition=business_hours_condition,  # Solo se ejecuta si la condición es True
        max_retries=0,
    )
    scheduler.add_task(business_hours_task)

    # Tarea de limpieza diaria a las 23:00
    daily_cleanup_task = Task(
        task_id="daily_cleanup",
        func=lambda: print(f"[{datetime.now()}] Daily cleanup executed!"),
        trigger_type="cron",
        trigger_args={"hour": 23, "minute": 0},
        max_retries=2,
    )
    scheduler.add_task(daily_cleanup_task)

    # Tarea de backup semanal (domingos a las 02:00)
    weekly_backup_task = Task(
        task_id="weekly_backup",
        func=lambda: print(f"[{datetime.now()}] Weekly backup executed!"),
        trigger_type="cron",
        trigger_args={"day_of_week": "sun", "hour": 2, "minute": 0},
        max_retries=3,
        retry_delay=300,  # 5 minutos entre reintentos
    )
    scheduler.add_task(weekly_backup_task)

    # =========================================================================
    # INICIAR SCHEDULER
    # =========================================================================
    print()
    print("=" * 80)
    print("🚀 Starting scheduler...")
    print("=" * 80)
    print()
    print("Active jobs:")
    scheduler.print_jobs()
    print()
    print("Press Ctrl+C to stop the scheduler")
    print("=" * 80)
    print()

    # Iniciar en modo blocking (nunca termina hasta Ctrl+C)
    scheduler.start(blocking=True)


def example_simple_usage():
    """Ejemplo de uso simplificado (método add_job)."""
    scheduler = Scheduler(timezone="UTC")

    # Añadir job simple cada minuto
    scheduler.add_job(
        func=lambda: print(f"[{datetime.now()}] Simple job executed!"),
        trigger="interval",
        job_id="simple_job",
        trigger_args={"seconds": 60},
        max_retries=2,
        retry_delay=10,
    )

    # Añadir job con cron expression
    scheduler.add_job(
        func=lambda: print(f"[{datetime.now()}] Cron job executed!"),
        trigger="cron",
        job_id="cron_job",
        trigger_args={"hour": "*/2", "minute": 0},  # Cada 2 horas
        max_retries=3,
        on_success=lambda r: print("✓ Cron job succeeded!"),
        on_failure=lambda e: print(f"✗ Cron job failed: {e}"),
    )

    # Iniciar scheduler
    scheduler.start(blocking=True)


def example_metrics_monitoring():
    """Ejemplo de monitoreo de métricas."""
    scheduler = Scheduler()

    # Añadir algunas tareas
    scheduler.add_job(
        func=lambda: time.sleep(1),
        trigger="interval",
        job_id="task1",
        trigger_args={"seconds": 5},
    )

    scheduler.add_job(
        func=lambda: time.sleep(0.5),
        trigger="interval",
        job_id="task2",
        trigger_args={"seconds": 10},
    )

    scheduler.start()

    # Monitorear métricas cada 15 segundos
    try:
        while True:
            time.sleep(15)
            metrics = scheduler.get_all_metrics()

            print("\n" + "=" * 60)
            print("METRICS REPORT")
            print("=" * 60)
            print(f"Uptime: {metrics['global']['uptime_seconds']:.0f}s")
            print(f"Total jobs executed: {metrics['global']['total_jobs_executed']}")
            print(f"Total failures: {metrics['global']['total_failures']}")
            print(f"Total retries: {metrics['global']['total_retries']}")
            print(f"Total tasks: {metrics['global']['total_tasks']}")
            print(f"Completed tasks: {metrics['global']['completed_tasks']}")

            print("\nPer-task metrics:")
            for task_id, task_metrics in metrics['tasks'].items():
                print(f"  {task_id}:")
                print(f"    - Total runs: {task_metrics['total_runs']}")
                print(f"    - Success rate: {task_metrics['success_rate']:.2%}")
                print(f"    - Avg duration: {task_metrics['avg_duration']:.2f}s")
                print(f"    - Last state: {task_metrics['last_state']}")
            print("=" * 60)

    except KeyboardInterrupt:
        print("\nStopping scheduler...")
        scheduler.shutdown(wait=True)


if __name__ == "__main__":
    # Ejecutar el ejemplo principal
    main()

    # Para ejecutar otros ejemplos, comenta main() y descomenta:
    # example_simple_usage()
    # example_metrics_monitoring()
