#!/usr/bin/env python3
"""
Script de prueba rápida del nuevo Scheduler mejorado.
Se ejecuta directamente sin necesidad de instalar el paquete completo.
"""

import sys
import time
from datetime import datetime
from pathlib import Path
import importlib.util

# Cargar el módulo scheduler directamente desde el archivo
scheduler_path = Path(__file__).parent.parent / "ctrutils" / "scheduler" / "scheduler.py"
spec = importlib.util.spec_from_file_location("scheduler_module", scheduler_path)
scheduler_module = importlib.util.module_from_spec(spec)
sys.modules["scheduler_module"] = scheduler_module
spec.loader.exec_module(scheduler_module)

# Importar las clases necesarias
Scheduler = scheduler_module.Scheduler
Task = scheduler_module.Task
JobState = scheduler_module.JobState

print("=" * 80)
print("SCHEDULER - Quick Test")
print("=" * 80)
print()

# Variables para tracking
execution_count = {"task1": 0, "task2": 0, "dependent": 0}
results = []


def task1():
    """Tarea simple 1."""
    execution_count["task1"] += 1
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Task 1 executed (count: {execution_count['task1']})")
    return "task1_result"


def task2():
    """Tarea simple 2."""
    execution_count["task2"] += 1
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Task 2 executed (count: {execution_count['task2']})")
    return "task2_result"


def task_dependent():
    """Tarea con dependencias."""
    execution_count["dependent"] += 1
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Dependent task executed (count: {execution_count['dependent']})")
    return "dependent_result"


def task_with_retry():
    """Tarea que falla las primeras 2 veces."""
    count = execution_count.get("retry_task", 0)
    execution_count["retry_task"] = count + 1

    if count < 2:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Retry task failed (attempt {count + 1})")
        raise Exception(f"Simulated failure (attempt {count + 1})")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Retry task succeeded!")
        return "retry_success"


def on_success(result):
    """Callback de éxito."""
    results.append(("success", result))
    print(f"  → Success callback: {result}")


def on_failure(exception):
    """Callback de fallo."""
    results.append(("failure", str(exception)))
    print(f"  → Failure callback: {exception}")


def on_retry(exception, attempt):
    """Callback de reintento."""
    print(f"  → Retry callback: attempt {attempt}, error: {exception}")


def main():
    """Test principal."""
    print("1. Creating scheduler...")
    scheduler = Scheduler(
        timezone="UTC",
        max_workers=3,
        coalesce=True,
    )
    print("   ✓ Scheduler created")
    print()

    # Test 1: Tareas simples con intervalo
    print("2. Adding simple tasks...")
    scheduler.add_job(
        func=task1,
        trigger="interval",
        job_id="simple_task_1",
        trigger_args={"seconds": 2},
        max_retries=1,
        on_success=on_success,
    )

    scheduler.add_job(
        func=task2,
        trigger="interval",
        job_id="simple_task_2",
        trigger_args={"seconds": 3},
        max_retries=1,
    )
    print("   ✓ Simple tasks added")
    print()

    # Test 2: Tarea con dependencias
    print("3. Adding task with dependencies...")

    # Primero la tarea independiente
    task_independent = Task(
        task_id="independent_task",
        func=lambda: print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Independent task"),
        trigger_type="interval",
        trigger_args={"seconds": 5},
        max_retries=1,
    )
    scheduler.add_task(task_independent)

    # Luego la dependiente
    task_dep = Task(
        task_id="dependent_task",
        func=task_dependent,
        trigger_type="interval",
        trigger_args={"seconds": 5},
        dependencies=["independent_task"],
        max_retries=1,
    )
    scheduler.add_task(task_dep)
    print("   ✓ Tasks with dependencies added")
    print()

    # Test 3: Tarea con reintentos
    print("4. Adding task with retries...")
    retry_task = Task(
        task_id="retry_task",
        func=task_with_retry,
        trigger_type="interval",
        trigger_args={"seconds": 4},
        max_retries=3,
        retry_delay=1,
        retry_backoff=1.5,
        on_success=on_success,
        on_failure=on_failure,
        on_retry=on_retry,
    )
    scheduler.add_task(retry_task)
    print("   ✓ Task with retries added")
    print()

    # Iniciar scheduler
    print("5. Starting scheduler...")
    scheduler.start()
    print("   ✓ Scheduler started")
    print()

    print("=" * 80)
    print("Scheduler is running! Watching for 15 seconds...")
    print("=" * 80)
    print()

    # Ejecutar por 15 segundos
    time.sleep(15)

    # Mostrar métricas
    print()
    print("=" * 80)
    print("METRICS REPORT")
    print("=" * 80)

    metrics = scheduler.get_all_metrics()

    print(f"\nGlobal Metrics:")
    print(f"  - Running: {metrics['global']['is_running']}")
    print(f"  - Total tasks: {metrics['global']['total_tasks']}")
    print(f"  - Completed tasks: {metrics['global']['completed_tasks']}")
    print(f"  - Total jobs executed: {metrics['global']['total_jobs_executed']}")
    print(f"  - Total failures: {metrics['global']['total_failures']}")
    print(f"  - Total retries: {metrics['global']['total_retries']}")
    print(f"  - Uptime: {metrics['global']['uptime_seconds']:.1f}s")

    print(f"\nPer-task Metrics:")
    for task_id, task_metrics in metrics['tasks'].items():
        print(f"\n  {task_id}:")
        print(f"    - Total runs: {task_metrics['total_runs']}")
        print(f"    - Successes: {task_metrics['successes']}")
        print(f"    - Failures: {task_metrics['failures']}")
        print(f"    - Retries: {task_metrics['retries']}")
        print(f"    - Success rate: {task_metrics['success_rate']:.1%}")
        print(f"    - Last state: {task_metrics['last_state']}")
        if task_metrics['avg_duration']:
            print(f"    - Avg duration: {task_metrics['avg_duration']:.2f}s")

    print()
    print("=" * 80)

    # Test de métricas individuales
    print("\nTesting individual task metrics...")
    task1_metrics = scheduler.get_task_metrics("simple_task_1")
    if task1_metrics:
        print(f"  ✓ Task 'simple_task_1' metrics retrieved")
        print(f"    Total runs: {task1_metrics['total_runs']}")

    # Verificar ejecuciones
    print(f"\nExecution counts:")
    print(f"  - task1: {execution_count['task1']}")
    print(f"  - task2: {execution_count['task2']}")
    print(f"  - dependent: {execution_count['dependent']}")
    print(f"  - retry_task: {execution_count.get('retry_task', 0)}")

    # Verificar callbacks
    print(f"\nCallback results: {len(results)} callbacks executed")

    # Test de control de scheduler
    print("\n" + "=" * 80)
    print("Testing scheduler control methods...")
    print("=" * 80)

    # Verificar estado
    print(f"\n  - is_running(): {scheduler.is_running()}")

    # Listar jobs
    jobs = scheduler.get_jobs()
    print(f"  - get_jobs(): {len(jobs)} jobs")

    # Pausar y reanudar
    print("\n  Testing pause/resume...")
    try:
        scheduler.pause_job("simple_task_1")
        print("    ✓ Job paused")
        scheduler.resume_job("simple_task_1")
        print("    ✓ Job resumed")
    except Exception as e:
        print(f"    ✗ Error: {e}")

    # Shutdown
    print("\n  Shutting down scheduler...")
    scheduler.shutdown(wait=True)
    print("    ✓ Scheduler shut down")
    print(f"  - is_running(): {scheduler.is_running()}")

    print()
    print("=" * 80)
    print("✓ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print()

    # Verificaciones finales
    assert execution_count["task1"] >= 5, "Task 1 should have executed at least 5 times"
    assert execution_count["task2"] >= 3, "Task 2 should have executed at least 3 times"
    assert not scheduler.is_running(), "Scheduler should be stopped"
    assert len(scheduler.tasks) == 5, "Should have 5 tasks"

    print("✓ All assertions passed!")
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
