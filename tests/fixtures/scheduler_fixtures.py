import time
from datetime import datetime, timedelta
from unittest.mock import Mock


def mock_job_success():
    time.sleep(0.01)
    return "success"


def mock_job_failure():
    time.sleep(0.01)
    raise ValueError("Mock job failed")


def mock_job_timeout():
    time.sleep(10)
    return "should timeout"


def mock_job_quick():
    return "quick"


def mock_job_with_args(arg1, arg2):
    return f"args: {arg1}, {arg2}"


def mock_job_with_kwargs(key1=None, key2=None):
    return f"kwargs: {key1}, {key2}"


def mock_job_with_exception(exception_type=ValueError):
    raise exception_type("Intentional exception")


def mock_job_slow(duration=1.0):
    time.sleep(duration)
    return f"completed after {duration}s"


def mock_job_counter():
    if not hasattr(mock_job_counter, 'count'):
        mock_job_counter.count = 0
    mock_job_counter.count += 1
    return mock_job_counter.count


def mock_job_with_state(state_dict):
    if 'counter' not in state_dict:
        state_dict['counter'] = 0
    state_dict['counter'] += 1
    return state_dict['counter']


def create_mock_callback(return_value=None, side_effect=None):
    mock_cb = Mock()
    if return_value is not None:
        mock_cb.return_value = return_value
    if side_effect is not None:
        mock_cb.side_effect = side_effect
    return mock_cb


def create_dependency_chain(length=3):
    return [f"task_{i}" for i in range(length)]


def create_circular_dependency():
    return {
        'task_a': ['task_b'],
        'task_b': ['task_c'],
        'task_c': ['task_a']
    }


def create_complex_dependency_graph():
    return {
        'task_1': [],
        'task_2': ['task_1'],
        'task_3': ['task_1'],
        'task_4': ['task_2', 'task_3'],
        'task_5': ['task_4'],
    }


def create_invalid_dependency_graph():
    return {
        'task_a': ['non_existent_task'],
        'task_b': ['task_a'],
    }


def create_timezone_test_cases():
    return [
        {'timezone': 'UTC', 'valid': True},
        {'timezone': 'America/New_York', 'valid': True},
        {'timezone': 'Europe/London', 'valid': True},
        {'timezone': 'Asia/Tokyo', 'valid': True},
        {'timezone': 'Invalid/Timezone', 'valid': False},
        {'timezone': '', 'valid': False},
        {'timezone': None, 'valid': False},
        {'timezone': 'GMT+5', 'valid': True},
        {'timezone': 'US/Eastern', 'valid': True},
        {'timezone': 'Australia/Sydney', 'valid': True},
    ]


def create_cron_expression_test_cases():
    return [
        {'expression': '* * * * *', 'description': 'every minute', 'valid': True},
        {'expression': '0 * * * *', 'description': 'every hour', 'valid': True},
        {'expression': '0 0 * * *', 'description': 'every day at midnight', 'valid': True},
        {'expression': '0 0 * * 0', 'description': 'every Sunday', 'valid': True},
        {'expression': '*/5 * * * *', 'description': 'every 5 minutes', 'valid': True},
        {'expression': '0 9-17 * * 1-5', 'description': 'weekdays 9am-5pm', 'valid': True},
        {'expression': 'invalid', 'description': 'invalid expression', 'valid': False},
        {'expression': '60 * * * *', 'description': 'invalid minute', 'valid': False},
        {'expression': '* 25 * * *', 'description': 'invalid hour', 'valid': False},
        {'expression': '', 'description': 'empty expression', 'valid': False},
    ]


def create_interval_test_cases():
    return [
        {'seconds': 1, 'valid': True},
        {'seconds': 60, 'valid': True},
        {'seconds': 3600, 'valid': True},
        {'seconds': 0.1, 'valid': True},
        {'seconds': 0, 'valid': False},
        {'seconds': -1, 'valid': False},
        {'seconds': None, 'valid': False},
    ]


def create_date_schedule_test_cases():
    now = datetime.now()
    return [
        {'date': now + timedelta(seconds=5), 'valid': True, 'description': 'future date'},
        {'date': now + timedelta(hours=1), 'valid': True, 'description': 'future hour'},
        {'date': now + timedelta(days=1), 'valid': True, 'description': 'future day'},
        {'date': now - timedelta(hours=1), 'valid': False, 'description': 'past date'},
        {'date': now - timedelta(days=1), 'valid': False, 'description': 'past day'},
        {'date': None, 'valid': False, 'description': 'None date'},
    ]


def create_retry_scenarios():
    return [
        {'max_retries': 0, 'backoff': 1, 'expected_attempts': 1},
        {'max_retries': 1, 'backoff': 1, 'expected_attempts': 2},
        {'max_retries': 3, 'backoff': 1, 'expected_attempts': 4},
        {'max_retries': 3, 'backoff': 2, 'expected_attempts': 4},
        {'max_retries': 5, 'backoff': 1.5, 'expected_attempts': 6},
    ]


def create_timeout_scenarios():
    return [
        {'timeout': 0.1, 'job_duration': 0.05, 'should_timeout': False},
        {'timeout': 0.1, 'job_duration': 0.2, 'should_timeout': True},
        {'timeout': 1.0, 'job_duration': 0.5, 'should_timeout': False},
        {'timeout': 0.5, 'job_duration': 1.0, 'should_timeout': True},
        {'timeout': None, 'job_duration': 10.0, 'should_timeout': False},
    ]


def create_callback_scenarios():
    return [
        {'callback_type': 'success', 'should_raise': False, 'exception': None},
        {'callback_type': 'success', 'should_raise': True, 'exception': ValueError},
        {'callback_type': 'failure', 'should_raise': False, 'exception': None},
        {'callback_type': 'failure', 'should_raise': True, 'exception': RuntimeError},
        {'callback_type': 'retry', 'should_raise': False, 'exception': None},
        {'callback_type': 'retry', 'should_raise': True, 'exception': Exception},
    ]


def create_concurrent_execution_scenarios():
    return [
        {'num_jobs': 1, 'max_workers': 1, 'expected_parallel': 1},
        {'num_jobs': 2, 'max_workers': 1, 'expected_parallel': 1},
        {'num_jobs': 5, 'max_workers': 2, 'expected_parallel': 2},
        {'num_jobs': 10, 'max_workers': 5, 'expected_parallel': 5},
        {'num_jobs': 3, 'max_workers': 10, 'expected_parallel': 3},
    ]


def create_job_state_modification_scenarios():
    return [
        {'action': 'pause', 'valid': True},
        {'action': 'resume', 'valid': True},
        {'action': 'remove', 'valid': True},
        {'action': 'reschedule', 'valid': True},
        {'action': 'modify_next_run_time', 'valid': True},
    ]


def create_metrics_test_data():
    return {
        'job_1': {
            'success_count': 10,
            'failure_count': 2,
            'retry_count': 3,
            'total_executions': 12,
            'last_execution': datetime.now(),
        },
        'job_2': {
            'success_count': 5,
            'failure_count': 5,
            'retry_count': 8,
            'total_executions': 10,
            'last_execution': datetime.now() - timedelta(hours=1),
        },
        'job_3': {
            'success_count': 0,
            'failure_count': 10,
            'retry_count': 20,
            'total_executions': 10,
            'last_execution': datetime.now() - timedelta(minutes=30),
        },
    }


def create_daylight_saving_test_cases():
    return [
        {
            'timezone': 'America/New_York',
            'date': datetime(2024, 3, 10, 2, 30),
            'description': 'Spring forward - invalid time'
        },
        {
            'timezone': 'America/New_York',
            'date': datetime(2024, 11, 3, 1, 30),
            'description': 'Fall back - ambiguous time'
        },
        {
            'timezone': 'Europe/London',
            'date': datetime(2024, 3, 31, 1, 30),
            'description': 'Spring forward GMT'
        },
        {
            'timezone': 'Europe/London',
            'date': datetime(2024, 10, 27, 1, 30),
            'description': 'Fall back GMT'
        },
    ]


def create_signal_handling_test_cases():
    return [
        {'signal': 'SIGINT', 'during_execution': True, 'expected': 'graceful_shutdown'},
        {'signal': 'SIGINT', 'during_execution': False, 'expected': 'immediate_shutdown'},
        {'signal': 'SIGTERM', 'during_execution': True, 'expected': 'graceful_shutdown'},
        {'signal': 'SIGTERM', 'during_execution': False, 'expected': 'immediate_shutdown'},
    ]


def create_thread_pool_scenarios():
    return [
        {'max_workers': 1, 'jobs_submitted': 1, 'expected': 'success'},
        {'max_workers': 1, 'jobs_submitted': 10, 'expected': 'queued'},
        {'max_workers': 5, 'jobs_submitted': 3, 'expected': 'success'},
        {'max_workers': 5, 'jobs_submitted': 10, 'expected': 'partial_queued'},
        {'max_workers': None, 'jobs_submitted': 10, 'expected': 'default_pool'},
    ]
