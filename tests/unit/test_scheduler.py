"""Tests unitarios para el Scheduler."""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from ctrutils.scheduler import Scheduler


class TestSchedulerInit(unittest.TestCase):
    """Tests para inicializacion del Scheduler."""

    def test_init_default(self):
        """Test inicializacion con valores por defecto."""
        scheduler = Scheduler()
        self.assertIsNotNone(scheduler.scheduler)

    def test_init_with_timezone(self):
        """Test inicializacion con timezone."""
        scheduler = Scheduler(timezone='America/New_York')
        self.assertIsNotNone(scheduler.scheduler)


class TestSchedulerJobManagement(unittest.TestCase):
    """Tests para gestion de jobs."""

    def setUp(self):
        """Setup para cada test."""
        self.scheduler = Scheduler()

    def tearDown(self):
        """Limpieza despues de cada test."""
        if self.scheduler and self.scheduler.scheduler.running:
            self.scheduler.shutdown()

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
        self.assertTrue(self.scheduler.scheduler.running)

        # Detener
        self.scheduler.shutdown()
        self.assertFalse(self.scheduler.scheduler.running)


if __name__ == '__main__':
    unittest.main()
