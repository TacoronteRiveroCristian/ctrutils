"""Tests unitarios para el Scheduler."""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import time
import threading

from ctrutils.scheduler import Scheduler, Task, JobState, JobMetrics


class TestJobMetrics(unittest.TestCase):
    """Tests para JobMetrics."""

    def test_record_success(self):
        """Test registrar ejecución exitosa."""
        metrics = JobMetrics()
        metrics.record_run(1.5, JobState.SUCCESS)

        self.assertEqual(metrics.total_runs, 1)
        self.assertEqual(metrics.successes, 1)
        self.assertEqual(metrics.failures, 0)
        self.assertEqual(metrics.last_duration, 1.5)
        self.assertEqual(metrics.last_state, JobState.SUCCESS)
        self.assertEqual(metrics.avg_duration, 1.5)

    def test_record_failure(self):
        """Test registrar ejecución fallida."""
        metrics = JobMetrics()
        metrics.record_run(2.0, JobState.FAILED)

        self.assertEqual(metrics.total_runs, 1)
        self.assertEqual(metrics.successes, 0)
        self.assertEqual(metrics.failures, 1)
        self.assertEqual(metrics.last_state, JobState.FAILED)

    def test_record_retry(self):
        """Test registrar reintento."""
        metrics = JobMetrics()
        metrics.record_run(1.0, JobState.RETRYING)

        self.assertEqual(metrics.retries, 1)
        self.assertEqual(metrics.last_state, JobState.RETRYING)

    def test_to_dict(self):
        """Test convertir métricas a diccionario."""
        metrics = JobMetrics()
        metrics.record_run(1.5, JobState.SUCCESS)

        result = metrics.to_dict()

        self.assertIn('total_runs', result)
        self.assertIn('success_rate', result)
        self.assertIn('avg_duration', result)
        self.assertEqual(result['total_runs'], 1)
        self.assertEqual(result['success_rate'], 1.0)


class TestTask(unittest.TestCase):
    """Tests para Task."""

    def test_task_creation(self):
        """Test crear una tarea."""
        mock_func = Mock()

        task = Task(
            task_id='test_task',
            func=mock_func,
            trigger_type='interval',
            trigger_args={'seconds': 60},
            max_retries=3,
            retry_delay=30,
        )

        self.assertEqual(task.task_id, 'test_task')
        self.assertEqual(task.func, mock_func)
        self.assertEqual(task.max_retries, 3)
        self.assertEqual(task.state, JobState.PENDING)

    def test_task_with_dependencies(self):
        """Test crear tarea con dependencias."""
        mock_func = Mock()

        task = Task(
            task_id='dependent_task',
            func=mock_func,
            trigger_type='cron',
            trigger_args={'minute': '0'},
            dependencies=['task1', 'task2'],
        )

        self.assertEqual(len(task.dependencies), 2)
        self.assertIn('task1', task.dependencies)


class TestSchedulerInit(unittest.TestCase):
    """Tests para inicializacion del Scheduler."""

    def test_init_default(self):
        """Test inicializacion con valores por defecto."""
        scheduler = Scheduler()
        self.assertIsNotNone(scheduler.scheduler)
        self.assertFalse(scheduler.is_running())
        self.assertEqual(len(scheduler.tasks), 0)

    def test_init_with_timezone(self):
        """Test inicializacion con timezone."""
        scheduler = Scheduler(timezone='America/New_York')
        self.assertIsNotNone(scheduler.scheduler)

    def test_init_with_max_workers(self):
        """Test inicializacion con max_workers."""
        scheduler = Scheduler(max_workers=5)
        self.assertIsNotNone(scheduler.scheduler)


class TestSchedulerJobManagement(unittest.TestCase):
    """Tests para gestion de jobs."""

    def setUp(self):
        """Setup para cada test."""
        self.scheduler = Scheduler()

    def tearDown(self):
        """Limpieza despues de cada test."""
        if self.scheduler and self.scheduler.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def test_add_job_interval(self):
        """Test añadir job con intervalo."""
        mock_func = Mock()

        self.scheduler.add_job(
            func=mock_func,
            trigger='interval',
            job_id='test_job',
            trigger_args={'seconds': 1}
        )

        jobs = self.scheduler.get_jobs()
        job_ids = [job.id for job in jobs]
        self.assertIn('test_job', job_ids)
        self.assertIn('test_job', self.scheduler.tasks)

    def test_add_job_cron(self):
        """Test añadir job con cron."""
        mock_func = Mock()

        self.scheduler.add_job(
            func=mock_func,
            trigger='cron',
            job_id='cron_job',
            trigger_args={'hour': 12, 'minute': 0}
        )

        jobs = self.scheduler.get_jobs()
        job_ids = [job.id for job in jobs]
        self.assertIn('cron_job', job_ids)

    def test_add_job_date(self):
        """Test añadir job con fecha especifica."""
        mock_func = Mock()
        run_date = datetime.now() + timedelta(hours=1)

        self.scheduler.add_job(
            func=mock_func,
            trigger='date',
            job_id='date_job',
            trigger_args={'run_date': run_date}
        )

        jobs = self.scheduler.get_jobs()
        job_ids = [job.id for job in jobs]
        self.assertIn('date_job', job_ids)

    def test_add_job_with_retries(self):
        """Test añadir job con reintentos."""
        mock_func = Mock()

        self.scheduler.add_job(
            func=mock_func,
            trigger='interval',
            job_id='retry_job',
            trigger_args={'seconds': 60},
            max_retries=5,
            retry_delay=30,
        )

        task = self.scheduler.tasks['retry_job']
        self.assertEqual(task.max_retries, 5)
        self.assertEqual(task.retry_delay, 30)

    def test_add_job_with_dependencies(self):
        """Test añadir job con dependencias."""
        mock_func = Mock()

        self.scheduler.add_job(
            func=mock_func,
            trigger='interval',
            job_id='job1',
            trigger_args={'seconds': 60},
        )

        self.scheduler.add_job(
            func=mock_func,
            trigger='interval',
            job_id='job2',
            trigger_args={'seconds': 60},
            dependencies=['job1'],
        )

        task = self.scheduler.tasks['job2']
        self.assertIn('job1', task.dependencies)

    def test_add_task(self):
        """Test añadir tarea usando Task object."""
        mock_func = Mock()

        task = Task(
            task_id='task_obj',
            func=mock_func,
            trigger_type='interval',
            trigger_args={'seconds': 30},
            max_retries=2,
        )

        self.scheduler.add_task(task)

        self.assertIn('task_obj', self.scheduler.tasks)
        jobs = self.scheduler.get_jobs()
        job_ids = [job.id for job in jobs]
        self.assertIn('task_obj', job_ids)

    def test_remove_job(self):
        """Test eliminar job."""
        mock_func = Mock()

        self.scheduler.add_job(
            func=mock_func,
            trigger='interval',
            job_id='removable_job',
            trigger_args={'seconds': 60}
        )

        # Eliminar
        self.scheduler.remove_job('removable_job')

        # Verificar que no existe
        jobs = self.scheduler.get_jobs()
        job_ids = [job.id for job in jobs]
        self.assertNotIn('removable_job', job_ids)
        self.assertNotIn('removable_job', self.scheduler.tasks)

    def test_get_jobs(self):
        """Test obtener lista de jobs."""
        mock_func = Mock()

        # Añadir varios jobs
        self.scheduler.add_job(
            mock_func, 'interval', 'job1', {'seconds': 60}
        )
        self.scheduler.add_job(
            mock_func, 'interval', 'job2', {'seconds': 120}
        )

        jobs = self.scheduler.get_jobs()
        self.assertGreaterEqual(len(jobs), 2)

    def test_start_stop(self):
        """Test iniciar y detener scheduler."""
        mock_func = Mock()
        self.scheduler.add_job(
            mock_func, 'interval', 'test_start_stop', {'seconds': 60}
        )

        # Iniciar
        self.scheduler.start()
        self.assertTrue(self.scheduler.is_running())

        # Detener
        self.scheduler.shutdown(wait=False)
        self.assertFalse(self.scheduler.is_running())


class TestSchedulerAdvancedFeatures(unittest.TestCase):
    """Tests para características avanzadas del scheduler."""

    def setUp(self):
        """Setup para cada test."""
        self.scheduler = Scheduler()

    def tearDown(self):
        """Limpieza despues de cada test."""
        if self.scheduler and self.scheduler.is_running():
            self.scheduler.shutdown(wait=False)

    def test_job_execution_with_success_callback(self):
        """Test ejecución de job con callback de éxito."""
        result_container = {'called': False, 'result': None}

        def test_func():
            return 'success'

        def on_success(result):
            result_container['called'] = True
            result_container['result'] = result

        self.scheduler.add_job(
            func=test_func,
            trigger='date',
            job_id='success_job',
            trigger_args={'run_date': datetime.now() + timedelta(seconds=1)},
            on_success=on_success,
        )

        self.scheduler.start()
        time.sleep(3)

        # El callback debería haber sido llamado
        self.assertTrue(result_container['called'])
        self.assertEqual(result_container['result'], 'success')

    def test_job_execution_with_failure_callback(self):
        """Test ejecución de job con callback de fallo."""
        failure_container = {'called': False, 'exception': None}

        def failing_func():
            raise ValueError('Test error')

        def on_failure(exception):
            failure_container['called'] = True
            failure_container['exception'] = exception

        self.scheduler.add_job(
            func=failing_func,
            trigger='date',
            job_id='failure_job',
            trigger_args={'run_date': datetime.now() + timedelta(seconds=1)},
            max_retries=0,  # Sin reintentos
            on_failure=on_failure,
        )

        self.scheduler.start()
        time.sleep(2)

        # El callback debería haber sido llamado
        self.assertTrue(failure_container['called'])
        self.assertIsInstance(failure_container['exception'], ValueError)

    def test_get_task_metrics(self):
        """Test obtener métricas de una tarea."""
        mock_func = Mock(return_value='ok')

        self.scheduler.add_job(
            func=mock_func,
            trigger='date',
            job_id='metrics_job',
            trigger_args={'run_date': datetime.now() + timedelta(seconds=1)},
        )

        self.scheduler.start()
        time.sleep(3)

        metrics = self.scheduler.get_task_metrics('metrics_job')

        self.assertIsNotNone(metrics)
        self.assertIn('total_runs', metrics)
        self.assertGreaterEqual(metrics['total_runs'], 1)

    def test_get_all_metrics(self):
        """Test obtener todas las métricas."""
        mock_func = Mock()

        self.scheduler.add_job(
            func=mock_func,
            trigger='interval',
            job_id='metric_job1',
            trigger_args={'seconds': 60},
        )

        self.scheduler.start()

        metrics = self.scheduler.get_all_metrics()

        self.assertIn('global', metrics)
        self.assertIn('tasks', metrics)
        self.assertIn('total_tasks', metrics['global'])
        self.assertIn('is_running', metrics['global'])
        self.assertTrue(metrics['global']['is_running'])

    def test_pause_resume_job(self):
        """Test pausar y reanudar job."""
        mock_func = Mock()

        self.scheduler.add_job(
            func=mock_func,
            trigger='interval',
            job_id='pausable_job',
            trigger_args={'seconds': 60},
        )

        self.scheduler.start()

        # Pausar
        self.scheduler.pause_job('pausable_job')
        job = self.scheduler.scheduler.get_job('pausable_job')
        # APScheduler no expone directamente el estado de pausa, pero no debería lanzar error

        # Reanudar
        self.scheduler.resume_job('pausable_job')

    def test_reschedule_job(self):
        """Test re-programar un job."""
        mock_func = Mock()

        self.scheduler.add_job(
            func=mock_func,
            trigger='interval',
            job_id='reschedulable_job',
            trigger_args={'seconds': 60},
        )

        # Re-programar con cron
        self.scheduler.reschedule_job(
            'reschedulable_job',
            'cron',
            hour=12,
            minute=0,
        )

        job = self.scheduler.scheduler.get_job('reschedulable_job')
        self.assertIsNotNone(job)

    def test_task_with_condition(self):
        """Test tarea con condición."""
        execution_container = {'count': 0}

        def test_func():
            execution_container['count'] += 1

        def condition():
            # Solo ejecutar la primera vez
            return execution_container['count'] == 0

        task = Task(
            task_id='conditional_task',
            func=test_func,
            trigger_type='interval',
            trigger_args={'seconds': 1},
            condition=condition,
        )

        self.scheduler.add_task(task)
        self.scheduler.start()

        time.sleep(3)

        # Solo debería haberse ejecutado una vez debido a la condición
        self.assertLessEqual(execution_container['count'], 1)

    def test_print_jobs(self):
        """Test imprimir jobs."""
        mock_func = Mock()

        self.scheduler.add_job(
            func=mock_func,
            trigger='interval',
            job_id='printable_job',
            trigger_args={'seconds': 60},
        )

        # No debería lanzar excepción
        self.scheduler.print_jobs()


if __name__ == '__main__':
    unittest.main()
