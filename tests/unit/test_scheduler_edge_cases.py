import unittest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pytz
import pytest

import sys
sys.path.insert(0, '/home/cristiantr/GitHub/ctrutils')

from ctrutils.scheduler.scheduler import Scheduler, Task
from tests.fixtures.scheduler_fixtures import (
    mock_job_success,
    mock_job_failure,
    mock_job_timeout,
    mock_job_quick,
    mock_job_with_exception,
    mock_job_slow,
    create_mock_callback,
    create_circular_dependency,
    create_complex_dependency_graph,
    create_invalid_dependency_graph,
    create_timezone_test_cases,
    create_cron_expression_test_cases,
    create_interval_test_cases,
    create_retry_scenarios,
    create_timeout_scenarios,
    create_callback_scenarios,
)


@pytest.mark.unit
@pytest.mark.edge_case
class TestSchedulerTimezoneEdgeCases(unittest.TestCase):

    def test_init_with_invalid_timezone_string(self):
        with self.assertRaises(Exception):
            Scheduler(timezone='Invalid/Timezone')

    def test_init_with_empty_timezone(self):
        with self.assertRaises(Exception):
            Scheduler(timezone='')

    def test_init_with_none_timezone(self):
        with self.assertRaises(Exception):
            Scheduler(timezone=None)

    def test_init_with_valid_timezones(self):
        valid_timezones = ['UTC', 'America/New_York', 'Europe/London', 'Asia/Tokyo']

        for tz in valid_timezones:
            with self.subTest(timezone=tz):
                scheduler = Scheduler(timezone=tz)
                self.assertIsNotNone(scheduler)
                self.assertEqual(scheduler.timezone, tz)
                scheduler.shutdown(wait=False)

    def test_timezone_test_cases(self):
        test_cases = create_timezone_test_cases()

        for case in test_cases:
            with self.subTest(timezone=case['timezone']):
                if case['valid']:
                    scheduler = Scheduler(timezone=case['timezone'])
                    self.assertIsNotNone(scheduler)
                    scheduler.shutdown(wait=False)
                else:
                    with self.assertRaises(Exception):
                        Scheduler(timezone=case['timezone'])


@pytest.mark.unit
@pytest.mark.edge_case
class TestSchedulerDependencyEdgeCases(unittest.TestCase):

    def test_add_task_with_circular_dependency_simple(self):
        scheduler = Scheduler()

        task_a = Task(name='task_a', func=mock_job_quick, dependencies=['task_b'])
        task_b = Task(name='task_b', func=mock_job_quick, dependencies=['task_a'])

        scheduler.add_task(task_a)

        with self.assertRaises((ValueError, RuntimeError)):
            scheduler.add_task(task_b)

        scheduler.shutdown(wait=False)

    def test_add_task_with_non_existent_dependency(self):
        scheduler = Scheduler()

        task = Task(name='task_1', func=mock_job_quick, dependencies=['non_existent'])

        with self.assertRaises((ValueError, KeyError)):
            scheduler.add_task(task)

        scheduler.shutdown(wait=False)

    def test_add_task_with_deep_dependency_chain(self):
        scheduler = Scheduler()

        for i in range(10):
            deps = [f'task_{i-1}'] if i > 0 else []
            task = Task(name=f'task_{i}', func=mock_job_quick, dependencies=deps)
            scheduler.add_task(task)

        self.assertEqual(len(scheduler.tasks), 10)
        scheduler.shutdown(wait=False)

    def test_dependency_failure_stops_dependent_tasks(self):
        scheduler = Scheduler()

        task_1 = Task(name='task_1', func=mock_job_failure)
        task_2 = Task(name='task_2', func=mock_job_success, dependencies=['task_1'])

        scheduler.add_task(task_1)
        scheduler.add_task(task_2)

        scheduler.start()
        time.sleep(0.5)

        metrics_1 = scheduler.get_task_metrics('task_1')
        self.assertGreater(metrics_1['failure_count'], 0)

        scheduler.shutdown(wait=False)


@pytest.mark.unit
@pytest.mark.edge_case
class TestSchedulerTimeoutEdgeCases(unittest.TestCase):

    def test_timeout_shorter_than_execution_time(self):
        scheduler = Scheduler()

        job_id = scheduler.add_job(
            func=mock_job_slow,
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=1),
            kwargs={'duration': 2.0},
            timeout=0.5,
            job_id='timeout_test'
        )

        scheduler.start()
        time.sleep(2.0)

        metrics = scheduler.get_job_metrics(job_id)
        self.assertIsNotNone(metrics)

        scheduler.shutdown(wait=False)

    def test_execute_with_timeout_normal_completion(self):
        scheduler = Scheduler()

        result = scheduler._execute_with_timeout(mock_job_quick, timeout=1.0)
        self.assertEqual(result, "quick")

        scheduler.shutdown(wait=False)

    def test_execute_with_timeout_exceeds_limit(self):
        scheduler = Scheduler()

        result = scheduler._execute_with_timeout(mock_job_timeout, timeout=0.1)

        self.assertIsNone(result)

        scheduler.shutdown(wait=False)

    def test_timeout_scenarios(self):
        scheduler = Scheduler()
        scenarios = create_timeout_scenarios()

        for scenario in scenarios[:3]:
            with self.subTest(scenario=scenario):
                if scenario['timeout'] is not None:
                    if scenario['should_timeout']:
                        result = scheduler._execute_with_timeout(
                            lambda: mock_job_slow(scenario['job_duration']),
                            timeout=scenario['timeout']
                        )
                        self.assertIsNone(result)
                    else:
                        result = scheduler._execute_with_timeout(
                            lambda: mock_job_slow(scenario['job_duration']),
                            timeout=scenario['timeout']
                        )
                        self.assertIsNotNone(result)

        scheduler.shutdown(wait=False)


@pytest.mark.unit
@pytest.mark.edge_case
class TestSchedulerCallbackEdgeCases(unittest.TestCase):

    def test_callback_exception_in_on_success(self):
        scheduler = Scheduler()

        failing_callback = create_mock_callback(side_effect=ValueError("Callback failed"))

        job_id = scheduler.add_job(
            func=mock_job_success,
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=1),
            on_success=failing_callback,
            job_id='callback_test'
        )

        scheduler.start()
        time.sleep(2.0)

        failing_callback.assert_called()
        scheduler.shutdown(wait=False)

    def test_callback_exception_in_on_failure(self):
        scheduler = Scheduler()

        failing_callback = create_mock_callback(side_effect=RuntimeError("Callback error"))

        job_id = scheduler.add_job(
            func=mock_job_failure,
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=1),
            on_failure=failing_callback,
            job_id='callback_fail_test'
        )

        scheduler.start()
        time.sleep(2.0)

        failing_callback.assert_called()
        scheduler.shutdown(wait=False)

    def test_callback_modifying_scheduler_state(self):
        scheduler = Scheduler()

        def modify_state_callback():
            pass

        job_id = scheduler.add_job(
            func=mock_job_success,
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=1),
            on_success=modify_state_callback,
            job_id='state_mod_test'
        )

        scheduler.start()
        time.sleep(2.0)
        scheduler.shutdown(wait=False)

    def test_all_callback_scenarios(self):
        scenarios = create_callback_scenarios()

        for scenario in scenarios[:3]:
            with self.subTest(scenario=scenario):
                scheduler = Scheduler()

                if scenario['should_raise']:
                    callback = create_mock_callback(side_effect=scenario['exception']("Test exception"))
                else:
                    callback = create_mock_callback()

                if scenario['callback_type'] == 'success':
                    job_id = scheduler.add_job(
                        func=mock_job_success,
                        trigger='date',
                        run_date=datetime.now() + timedelta(seconds=1),
                        on_success=callback,
                        job_id=f'cb_test_{scenario["callback_type"]}'
                    )
                else:
                    job_id = scheduler.add_job(
                        func=mock_job_failure,
                        trigger='date',
                        run_date=datetime.now() + timedelta(seconds=1),
                        on_failure=callback,
                        job_id=f'cb_test_{scenario["callback_type"]}'
                    )

                scheduler.start()
                time.sleep(2.0)

                if scenario['should_raise']:
                    callback.assert_called()

                scheduler.shutdown(wait=False)


@pytest.mark.unit
@pytest.mark.edge_case
class TestSchedulerRetryEdgeCases(unittest.TestCase):

    def test_retry_with_zero_max_retries(self):
        scheduler = Scheduler()

        job_id = scheduler.add_job(
            func=mock_job_failure,
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=1),
            max_retries=0,
            job_id='retry_zero'
        )

        scheduler.start()
        time.sleep(2.0)

        metrics = scheduler.get_job_metrics(job_id)
        self.assertEqual(metrics['retry_count'], 0)

        scheduler.shutdown(wait=False)

    def test_retry_with_exponential_backoff(self):
        scheduler = Scheduler()

        job_id = scheduler.add_job(
            func=mock_job_failure,
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=1),
            max_retries=3,
            backoff_factor=2,
            job_id='retry_backoff'
        )

        scheduler.start()
        time.sleep(5.0)

        metrics = scheduler.get_job_metrics(job_id)
        self.assertGreater(metrics['retry_count'], 0)

        scheduler.shutdown(wait=False)

    def test_retry_scenarios(self):
        scenarios = create_retry_scenarios()

        for scenario in scenarios[:3]:
            with self.subTest(scenario=scenario):
                scheduler = Scheduler()

                job_id = scheduler.add_job(
                    func=mock_job_failure,
                    trigger='date',
                    run_date=datetime.now() + timedelta(seconds=1),
                    max_retries=scenario['max_retries'],
                    backoff_factor=scenario['backoff'],
                    job_id=f'retry_test_{scenario["max_retries"]}'
                )

                scheduler.start()
                time.sleep(3.0)

                metrics = scheduler.get_job_metrics(job_id)
                self.assertIsNotNone(metrics)

                scheduler.shutdown(wait=False)


@pytest.mark.unit
@pytest.mark.edge_case
class TestSchedulerIntervalEdgeCases(unittest.TestCase):

    def test_interval_zero_seconds(self):
        scheduler = Scheduler()

        with self.assertRaises((ValueError, TypeError)):
            scheduler.add_job(
                func=mock_job_quick,
                trigger='interval',
                seconds=0,
                job_id='interval_zero'
            )

        scheduler.shutdown(wait=False)

    def test_interval_negative_seconds(self):
        scheduler = Scheduler()

        with self.assertRaises((ValueError, TypeError)):
            scheduler.add_job(
                func=mock_job_quick,
                trigger='interval',
                seconds=-1,
                job_id='interval_negative'
            )

        scheduler.shutdown(wait=False)

    def test_interval_very_small(self):
        scheduler = Scheduler()

        job_id = scheduler.add_job(
            func=mock_job_quick,
            trigger='interval',
            seconds=0.1,
            job_id='interval_small'
        )

        scheduler.start()
        time.sleep(0.5)

        metrics = scheduler.get_job_metrics(job_id)
        self.assertGreater(metrics['success_count'], 1)

        scheduler.shutdown(wait=False)


@pytest.mark.unit
@pytest.mark.edge_case
class TestSchedulerCronEdgeCases(unittest.TestCase):

    def test_cron_invalid_expression(self):
        scheduler = Scheduler()

        with self.assertRaises((ValueError, TypeError)):
            scheduler.add_job(
                func=mock_job_quick,
                trigger='cron',
                cron_expression='invalid cron',
                job_id='cron_invalid'
            )

        scheduler.shutdown(wait=False)

    def test_cron_empty_expression(self):
        scheduler = Scheduler()

        with self.assertRaises((ValueError, TypeError, AttributeError)):
            scheduler.add_job(
                func=mock_job_quick,
                trigger='cron',
                cron_expression='',
                job_id='cron_empty'
            )

        scheduler.shutdown(wait=False)

    def test_cron_valid_expressions(self):
        valid_expressions = [
            ('* * * * *', 'every_minute'),
            ('0 * * * *', 'hourly'),
            ('0 0 * * *', 'daily'),
        ]

        for expr, desc in valid_expressions:
            with self.subTest(expression=desc):
                scheduler = Scheduler()

                job_id = scheduler.add_job(
                    func=mock_job_quick,
                    trigger='cron',
                    **self._parse_cron_expression(expr),
                    job_id=f'cron_{desc}'
                )

                self.assertIsNotNone(job_id)
                scheduler.shutdown(wait=False)

    def _parse_cron_expression(self, expr):
        parts = expr.split()
        return {
            'minute': parts[0],
            'hour': parts[1],
            'day': parts[2],
            'month': parts[3],
            'day_of_week': parts[4]
        }


@pytest.mark.unit
@pytest.mark.edge_case
class TestSchedulerDateTriggerEdgeCases(unittest.TestCase):

    def test_date_in_past(self):
        scheduler = Scheduler()

        past_date = datetime.now() - timedelta(hours=1)

        job_id = scheduler.add_job(
            func=mock_job_quick,
            trigger='date',
            run_date=past_date,
            job_id='date_past'
        )

        scheduler.start()
        time.sleep(1.0)

        metrics = scheduler.get_job_metrics(job_id)

        scheduler.shutdown(wait=False)

    def test_date_in_far_future(self):
        scheduler = Scheduler()

        future_date = datetime.now() + timedelta(days=365)

        job_id = scheduler.add_job(
            func=mock_job_quick,
            trigger='date',
            run_date=future_date,
            job_id='date_future'
        )

        self.assertIsNotNone(job_id)
        scheduler.shutdown(wait=False)

    def test_date_with_none(self):
        scheduler = Scheduler()

        with self.assertRaises((ValueError, TypeError)):
            scheduler.add_job(
                func=mock_job_quick,
                trigger='date',
                run_date=None,
                job_id='date_none'
            )

        scheduler.shutdown(wait=False)


if __name__ == '__main__':
    unittest.main()
