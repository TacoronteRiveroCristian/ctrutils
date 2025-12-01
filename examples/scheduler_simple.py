#!/usr/bin/env python3
"""
Ejemplo simple y minimalista del Scheduler mejorado.
Demuestra el uso básico para ejecutar tareas programadas continuamente.
"""

from ctrutils.scheduler import Scheduler, Task
from datetime import datetime
import time


def tarea_cada_minuto():
    """Tarea que se ejecuta cada minuto."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⏰ Tarea ejecutada cada minuto")


def tarea_cada_5_minutos():
    """Tarea que se ejecuta cada 5 minutos."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⏰ Tarea ejecutada cada 5 minutos")


def backup_diario():
    """Backup diario a las 02:00."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 💾 Ejecutando backup diario...")
    # Tu código de backup aquí
    time.sleep(2)  # Simula trabajo
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ Backup completado")


def main():
    """Ejemplo principal."""
    print("=" * 80)
    print("SCHEDULER SIMPLE - Ejecución Continua")
    print("=" * 80)
    print()

    # Crear scheduler
    scheduler = Scheduler(
        timezone="Europe/Madrid",  # Tu zona horaria
        max_workers=5,  # Máximo 5 tareas simultáneas
    )

    # Tarea 1: Cada minuto (usando add_job - método simple)
    scheduler.add_job(
        func=tarea_cada_minuto,
        trigger="cron",
        job_id="tarea_minuto",
        trigger_args={"minute": "*"},  # Cada minuto
    )

    # Tarea 2: Cada 5 minutos (usando Task - método avanzado)
    tarea_5min = Task(
        task_id="tarea_5_minutos",
        func=tarea_cada_5_minutos,
        trigger_type="cron",
        trigger_args={"minute": "*/5"},  # Cada 5 minutos
        max_retries=2,  # Reintentar 2 veces si falla
    )
    scheduler.add_task(tarea_5min)

    # Tarea 3: Backup diario a las 02:00
    backup_task = Task(
        task_id="backup_diario",
        func=backup_diario,
        trigger_type="cron",
        trigger_args={"hour": 2, "minute": 0},  # Todos los días a las 02:00
        max_retries=3,
        retry_delay=300,  # 5 minutos entre reintentos
        on_success=lambda r: print("✅ Backup completado con éxito"),
        on_failure=lambda e: print(f"❌ Error en backup: {e}"),
    )
    scheduler.add_task(backup_task)

    # Mostrar tareas programadas
    print("📋 Tareas programadas:")
    scheduler.print_jobs()
    print()

    # Iniciar scheduler en modo continuo (NUNCA TERMINA)
    print("🚀 Iniciando scheduler...")
    print("   Presiona Ctrl+C para detener")
    print("=" * 80)
    print()

    try:
        scheduler.start(blocking=True)  # ← CLAVE: blocking=True hace que nunca termine
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo scheduler...")
        scheduler.shutdown(wait=True)
        print("✅ Scheduler detenido correctamente")


if __name__ == "__main__":
    main()
