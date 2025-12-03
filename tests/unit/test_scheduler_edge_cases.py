import unittest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import pytz
import pytest

import sys
sys.path.insert(0, '/home/cristiantr/GitHub/ctrutils')

from ctrutils.scheduler.scheduler import Scheduler, Task
from tests.fixtures.scheduler_fixtures import (
    mock_job_success,
    mock_job_failure,
    mock_job_quick,
    mock_job_slow,
    create_mock_callback,
)


@pytest.mark.unit
@pytest.mark.edge_case
class TestSchedulerTimezoneEdgeCases(unittest.TestCase):

    def test_init_with_valid_timezone_utc(self):
        scheduler = Scheduler(timezone='UTC')
        self.assertIsNotNone(scheduler)
        self.assertEqual(str(scheduler.scheduler.timezone), 'UTC')
        scheduler.shutdown(wait=False)

    def test_init_with_valid_timezone_newyork(self):
        scheduler = Scheduler(timezone='America/New_York')
        self.assertIsNotNone(scheduler)
        self.assertEqual(str(scheduler.scheduler.timezone), 'America/New_York')
        scheduler.shutdown(wait=False)

    def test_init_with_valid_timezone_tokyo(self):
        scheduler = Scheduler(timezone='Asia/Tokyo')
        self.assertIsNotNone(scheduler)
        scheduler.shutdown(wait=False)


@pytest.mark.unit
@pytest.mark.edge_case
class TestSchedulerDependencyEdgeCases(unittest.TestCase):

    def test_add_task_with_valid_dependency(self):
        scheduler = Scheduler()

        task_1 = Task(
            task_id='task_1',
            func=mock_job_quick,
            trigger_type='date',
            trigger_args={'run_date': datetime.now() + timedelta(seconds=1)}
        )
        task_2 = Task(
            task_id='task_2',
            func=mock_job_quick,
            trigger_type='date',
            trigger_args={'run_date': datetime.now() + timedelta(seconds=2)},
            dependencies=['task_1']
        )

        scheduler.add_task(task_1)
        scheduler.add_task(task_2)

        self.assertEqual(len(scheduler.tasks), 2)
        scheduler.shutdown(wait=False)

    def test_add_task_with_deep_dependency_chain(self):
        scheduler = Scheduler()

        for i in range(5):
            deps = [f'task_{i-1}'] if i > 0 else []
            task = Task(
                task_id=f'task_{i}',
                func=mock_job_quick,
                trigger_type='date',
                trigger_args={'run_date': datetime.now() + timedelta(seconds=i+1)},
                dependencies=deps
            )
            scheduler.add_task(task)

        self.assertEqual(len(scheduler.tasks), 5)
        scheduler.shutdown(wait=False)


@pytest.mark.unit
@pytest.mark.edge_case
class TestSchedulerTimeoutEdgeCases(unittest.TestCase):

    def test_execute_with_timeout_normal_completion(self):
        scheduler = Scheduler()

        result = scheduler._execute_with_timeout(
            mock_job_quick,
            args=(),
            kwargs={},
            timeout=1
        )
        self.assertEqual(result, "quick")

        scheduler.shutdown(wait=False)

    def test_execute_with_timeout_exceeds_limit(self):
        scheduler = Scheduler()

        def slow_job():
            time.sleep(10)
            return "slow"

        with self.assertRaises(TimeoutError):
            scheduler._execute_with_timeout(
                slow_job,
                args=(),
                kwargs={},
                timeout=0.1
            )

        scheduler.shutdown(wait=False)


if __name__ == '__main__':
    unittest.main()
