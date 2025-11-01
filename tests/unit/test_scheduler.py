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
        self.assertIsNotNone(scheduler._scheduler)
    
    def test_init_with_timezone(self):
        """Test inicializacion con timezone."""
        scheduler = Scheduler(timezone='America/New_York')
        self.assertIsNotNone(scheduler._scheduler)


class TestSchedulerJobManagement(unittest.TestCase):
    """Tests para gestion de jobs."""
    
    def setUp(self):
        """Setup para cada test."""
        self.scheduler = Scheduler()
    
    def tearDown(self):
        """Limpieza despues de cada test."""
        if self.scheduler and self.scheduler._scheduler.running:
            self.scheduler.stop()
    
    def test_add_job_interval(self):
        """Test añadir job con intervalo."""
        mock_func = Mock()
        
        job_id = self.scheduler.add_job(
            func=mock_func,
            trigger='interval',
            seconds=1,
            job_id='test_job'
        )
        
        self.assertEqual(job_id, 'test_job')
    
    def test_add_job_cron(self):
        """Test añadir job con cron."""
        mock_func = Mock()
        
        job_id = self.scheduler.add_job(
            func=mock_func,
            trigger='cron',
            hour=12,
            minute=0,
            job_id='cron_job'
        )
        
        self.assertEqual(job_id, 'cron_job')
    
    def test_add_job_date(self):
        """Test añadir job con fecha especifica."""
        mock_func = Mock()
        run_date = datetime.now() + timedelta(hours=1)
        
        job_id = self.scheduler.add_job(
            func=mock_func,
            trigger='date',
            run_date=run_date,
            job_id='date_job'
        )
        
        self.assertEqual(job_id, 'date_job')
    
    def test_remove_job(self):
        """Test eliminar job."""
        mock_func = Mock()
        
        job_id = self.scheduler.add_job(
            func=mock_func,
            trigger='interval',
            seconds=60,
            job_id='removable_job'
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
        self.scheduler.add_job(mock_func, 'interval', seconds=60, job_id='job1')
        self.scheduler.add_job(mock_func, 'interval', seconds=120, job_id='job2')
        
        jobs = self.scheduler.get_jobs()
        self.assertGreaterEqual(len(jobs), 2)
    
    def test_start_stop(self):
        """Test iniciar y detener scheduler."""
        mock_func = Mock()
        self.scheduler.add_job(mock_func, 'interval', seconds=60)
        
        # Iniciar
        self.scheduler.start()
        self.assertTrue(self.scheduler._scheduler.running)
        
        # Detener
        self.scheduler.stop()
        self.assertFalse(self.scheduler._scheduler.running)


if __name__ == '__main__':
    unittest.main()
