import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from influxdb import InfluxDBClient


def create_mock_influxdb_client(
    ping_return=True,
    create_database_return=None,
    write_points_return=True,
    query_return=None,
    get_list_database_return=None,
    drop_database_return=None,
):
    mock_client = Mock(spec=InfluxDBClient)
    mock_client.ping.return_value = ping_return
    mock_client.create_database.return_value = create_database_return
    mock_client.write_points.return_value = write_points_return
    mock_client.query.return_value = query_return if query_return is not None else MagicMock()
    mock_client.get_list_database.return_value = (
        get_list_database_return if get_list_database_return is not None else []
    )
    mock_client.drop_database.return_value = drop_database_return
    mock_client.switch_database.return_value = None
    mock_client.close.return_value = None

    return mock_client


def create_edge_case_dataframe(case_type='infinity'):
    base_time = pd.date_range(start='2024-01-01', periods=10, freq='1min')

    if case_type == 'infinity':
        data = {
            'value1': [float('inf'), -float('inf'), 1.0, 2.0, float('inf'),
                      -float('inf'), 3.0, 4.0, float('inf'), -float('inf')],
            'value2': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        }
    elif case_type == 'all_nan':
        data = {
            'value1': [np.nan] * 10,
            'value2': [None] * 10
        }
    elif case_type == 'mixed_nan':
        data = {
            'value1': [np.nan, pd.NA, None, 1.0, math.nan, 2.0, np.nan, pd.NA, None, 3.0],
            'value2': [1.0, np.nan, None, pd.NA, math.nan, 4.0, 5.0, np.nan, None, 6.0]
        }
    elif case_type == 'empty':
        data = {
            'value1': [],
            'value2': []
        }
        base_time = pd.DatetimeIndex([])
    elif case_type == 'large_numbers':
        data = {
            'value1': [1e308, -1e308, 1e-308, -1e-308, 1e100, -1e100, 1e-100, -1e-100, 0.0, 1.0],
            'value2': [np.finfo(np.float64).max, np.finfo(np.float64).min, 0.0, 1.0, -1.0,
                      np.finfo(np.float32).max, np.finfo(np.float32).min, 100.0, 200.0, 300.0]
        }
    elif case_type == 'unicode':
        data = {
            'sensor': ['température', '温度', 'температура', 'θερμοκρασία', '🌡️',
                      'café', '北京', 'Москва', 'Αθήνα', 'emoji😀'],
            'location': ['París', '东京', 'Москва́', 'Ελλάδα', 'Test🏠',
                        'España', '上海', 'Сибирь', 'Κρήτη', 'Unicode✅']
        }
    elif case_type == 'empty_strings':
        data = {
            'value1': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            'tag1': ['', '   ', '\t', '\n', 'valid', '', '  \t  ', '\n\n', 'test', '']
        }
    elif case_type == 'special_chars':
        data = {
            'value1': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            'tag1': ['key=value', 'a,b,c', 'x y z', 'a"b"c', "a'b'c",
                    'a\\b\\c', 'a/b/c', 'a|b|c', 'a&b&c', 'a;b;c']
        }
    elif case_type == 'numpy_types':
        data = {
            'int8': np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=np.int8),
            'int16': np.array([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000], dtype=np.int16),
            'int32': np.array([1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000], dtype=np.int32),
            'int64': np.array([10000, 20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000], dtype=np.int64),
            'float32': np.array([1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8, 9.9, 10.1], dtype=np.float32),
            'float64': np.array([1.11, 2.22, 3.33, 4.44, 5.55, 6.66, 7.77, 8.88, 9.99, 10.11], dtype=np.float64),
        }
    elif case_type == 'boolean':
        data = {
            'bool_val': [True, False, True, False, True, False, True, False, True, False],
            'np_bool': np.array([True, False, True, False, True, False, True, False, True, False], dtype=bool)
        }
    else:
        data = {
            'value1': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            'value2': [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
        }

    df = pd.DataFrame(data, index=base_time)
    return df


def create_edge_case_points(case_type='infinity'):
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    if case_type == 'infinity':
        points = [
            {
                "measurement": "test",
                "tags": {"location": "lab"},
                "time": (base_time + timedelta(minutes=i)).isoformat(),
                "fields": {"value": float('inf') if i % 2 == 0 else -float('inf')}
            }
            for i in range(5)
        ]
    elif case_type == 'all_nan':
        points = [
            {
                "measurement": "test",
                "tags": {"location": "lab"},
                "time": (base_time + timedelta(minutes=i)).isoformat(),
                "fields": {"value": np.nan}
            }
            for i in range(5)
        ]
    elif case_type == 'empty_fields':
        points = [
            {
                "measurement": "test",
                "tags": {"location": "lab"},
                "time": (base_time + timedelta(minutes=i)).isoformat(),
                "fields": {}
            }
            for i in range(5)
        ]
    elif case_type == 'mixed_valid_invalid':
        points = [
            {
                "measurement": "test",
                "tags": {"location": "lab"},
                "time": (base_time + timedelta(minutes=i)).isoformat(),
                "fields": {
                    "value1": 1.0 if i % 2 == 0 else np.nan,
                    "value2": 2.0 if i % 3 == 0 else None,
                    "value3": 3.0
                }
            }
            for i in range(5)
        ]
    elif case_type == 'special_char_tags':
        points = [
            {
                "measurement": "test",
                "tags": {
                    "location": "key=value",
                    "sensor": "a,b,c",
                    "device": 'x"y"z'
                },
                "time": (base_time + timedelta(minutes=i)).isoformat(),
                "fields": {"value": float(i)}
            }
            for i in range(5)
        ]
    elif case_type == 'unicode_measurement':
        points = [
            {
                "measurement": "température_capteur",
                "tags": {"location": "París", "device": "温度计"},
                "time": (base_time + timedelta(minutes=i)).isoformat(),
                "fields": {"value": float(i), "label": f"測試{i}"}
            }
            for i in range(5)
        ]
    elif case_type == 'empty_list':
        points = []
    elif case_type == 'missing_measurement':
        points = [
            {
                "tags": {"location": "lab"},
                "time": (base_time + timedelta(minutes=i)).isoformat(),
                "fields": {"value": float(i)}
            }
            for i in range(5)
        ]
    else:
        points = [
            {
                "measurement": "test",
                "tags": {"location": "lab"},
                "time": (base_time + timedelta(minutes=i)).isoformat(),
                "fields": {"value": float(i)}
            }
            for i in range(5)
        ]

    return points


def create_malformed_query_examples():
    return [
        'SELECT * FROM',
        'SELECT FROM measurement',
        'SELECT * WHERE value > 10',
        'SELECT * FROM measurement WHERE',
        'SELECT * FROM measurement GROUP BY',
        'SELECT * FROM measurement WHERE value >',
        'SELECT * FROM "unclosed_quote',
        'SELECT * FROM measurement WHERE value = "unclosed',
        'SELECT COUNT() FROM measurement',
        'SELECT * FROM measurement LIMIT',
        'SELECT * FROM measurement ORDER BY',
        'SELECT * FROM measurement WHERE time >',
        'INVALID SQL SYNTAX',
        '',
        '   ',
    ]


def create_connection_failure_scenarios():
    return [
        {'host': 'invalid_host', 'port': 8086, 'error': 'Connection refused'},
        {'host': 'localhost', 'port': 99999, 'error': 'Invalid port'},
        {'host': '192.168.255.255', 'port': 8086, 'error': 'Network unreachable'},
        {'host': '', 'port': 8086, 'error': 'Empty host'},
        {'host': 'localhost', 'port': -1, 'error': 'Negative port'},
        {'host': 'localhost', 'port': 0, 'error': 'Zero port'},
        {'host': None, 'port': 8086, 'error': 'None host'},
        {'host': 'localhost', 'port': None, 'error': 'None port'},
    ]


def create_batch_size_scenarios():
    return [
        {'batch_size': 0, 'expected': 'ValueError'},
        {'batch_size': -1, 'expected': 'ValueError'},
        {'batch_size': 1, 'expected': 'success'},
        {'batch_size': 100, 'expected': 'success'},
        {'batch_size': 5000, 'expected': 'success'},
        {'batch_size': 10000, 'expected': 'success'},
        {'batch_size': None, 'expected': 'use_default'},
    ]


def create_timezone_scenarios():
    return [
        {'timezone': 'UTC', 'expected': 'success'},
        {'timezone': 'America/New_York', 'expected': 'success'},
        {'timezone': 'Europe/London', 'expected': 'success'},
        {'timezone': 'Asia/Tokyo', 'expected': 'success'},
        {'timezone': 'Invalid/Timezone', 'expected': 'error'},
        {'timezone': '', 'expected': 'error'},
        {'timezone': None, 'expected': 'error'},
        {'timezone': 'GMT+5', 'expected': 'success'},
        {'timezone': 'US/Eastern', 'expected': 'success'},
    ]


def create_retention_policy_scenarios():
    return [
        {'name': 'test_rp', 'duration': '1d', 'replication': 1, 'default': False},
        {'name': 'test_rp', 'duration': '1w', 'replication': 1, 'default': True},
        {'name': 'test_rp', 'duration': 'INF', 'replication': 1, 'default': False},
        {'name': 'test_rp', 'duration': '0', 'replication': 1, 'default': False},
        {'name': '', 'duration': '1d', 'replication': 1, 'default': False},
        {'name': 'test_rp', 'duration': '', 'replication': 1, 'default': False},
        {'name': 'test_rp', 'duration': '1d', 'replication': 0, 'default': False},
        {'name': 'test_rp', 'duration': 'invalid', 'replication': 1, 'default': False},
    ]


def create_value_normalization_test_cases():
    return [
        {'value': None, 'expected': None, 'description': 'None value'},
        {'value': np.nan, 'expected': None, 'description': 'numpy.nan'},
        {'value': pd.NA, 'expected': None, 'description': 'pandas.NA'},
        {'value': math.nan, 'expected': None, 'description': 'math.nan'},
        {'value': float('inf'), 'expected': None, 'description': 'positive infinity'},
        {'value': float('-inf'), 'expected': None, 'description': 'negative infinity'},
        {'value': 1, 'expected': 1, 'description': 'int'},
        {'value': 1.5, 'expected': 1.5, 'description': 'float'},
        {'value': 'test', 'expected': 'test', 'description': 'string'},
        {'value': '', 'expected': '', 'description': 'empty string'},
        {'value': '   ', 'expected': '   ', 'description': 'whitespace string'},
        {'value': True, 'expected': True, 'description': 'boolean True'},
        {'value': False, 'expected': False, 'description': 'boolean False'},
        {'value': np.int8(10), 'expected': 10, 'description': 'numpy.int8'},
        {'value': np.int16(100), 'expected': 100, 'description': 'numpy.int16'},
        {'value': np.int32(1000), 'expected': 1000, 'description': 'numpy.int32'},
        {'value': np.int64(10000), 'expected': 10000, 'description': 'numpy.int64'},
        {'value': np.float32(1.5), 'expected': 1.5, 'description': 'numpy.float32'},
        {'value': np.float64(2.5), 'expected': 2.5, 'description': 'numpy.float64'},
        {'value': np.bool_(True), 'expected': True, 'description': 'numpy.bool_'},
        {'value': 1e308, 'expected': 1e308, 'description': 'very large number'},
        {'value': 1e-308, 'expected': 1e-308, 'description': 'very small number'},
        {'value': 0.0, 'expected': 0.0, 'description': 'zero float'},
        {'value': -0.0, 'expected': -0.0, 'description': 'negative zero'},
        {'value': '北京', 'expected': '北京', 'description': 'Chinese characters'},
        {'value': 'Москва', 'expected': 'Москва', 'description': 'Cyrillic characters'},
        {'value': 'café', 'expected': 'café', 'description': 'accented characters'},
        {'value': '🌡️', 'expected': '🌡️', 'description': 'emoji'},
    ]


def create_comprehensive_mock_client(
    ping_success=True,
    query_results=None,
    write_success=True,
    databases=None,
    measurements=None,
    error_on_query=None,
    error_on_write=None,
):
    """
    Create a comprehensive mock InfluxDB client with all commonly used methods.

    Args:
        ping_success: Whether ping() should return True
        query_results: List of mock query results or single result
        write_success: Whether write_points() should return True
        databases: List of database dicts for get_list_database()
        measurements: List of measurements for query() results
        error_on_query: Exception to raise on query()
        error_on_write: Exception to raise on write_points()
    """
    mock_client = Mock(spec=InfluxDBClient)

    mock_client.ping.return_value = ping_success
    mock_client.write_points.return_value = write_success

    if error_on_write:
        mock_client.write_points.side_effect = error_on_write

    if error_on_query:
        mock_client.query.side_effect = error_on_query
    elif query_results is not None:
        if isinstance(query_results, list):
            mock_client.query.side_effect = query_results
        else:
            mock_client.query.return_value = query_results
    else:
        mock_client.query.return_value = MagicMock()

    if databases is None:
        databases = [{'name': 'test_db'}]
    mock_client.get_list_database.return_value = databases

    mock_client.create_database.return_value = None
    mock_client.drop_database.return_value = None
    mock_client.switch_database.return_value = None
    mock_client.close.return_value = None
    mock_client.drop_measurement.return_value = None

    return mock_client


def create_mock_query_result(points_data=None, raw_data=None):
    """
    Create a mock ResultSet from InfluxDB query.

    Args:
        points_data: List of point dicts with 'time' and field keys
        raw_data: Raw data dict if you want full control
    """
    mock_result = MagicMock()

    if raw_data:
        mock_result.raw = raw_data
    elif points_data:
        mock_result.raw = {
            'series': [{
                'name': 'test_measurement',
                'columns': ['time'] + list(points_data[0].keys() - {'time'}),
                'values': [[p['time']] + [p[k] for k in points_data[0].keys() if k != 'time']
                          for p in points_data]
            }]
        }
    else:
        mock_result.raw = {'series': []}

    def get_points():
        if points_data:
            return iter(points_data)
        return iter([])

    mock_result.get_points.side_effect = get_points
    mock_result.__iter__ = lambda self: iter([mock_result])

    return mock_result


def create_test_dataframe(
    rows=100,
    num_fields=3,
    num_tags=2,
    with_nans=False,
    nan_percentage=0.1,
    start_time=None,
    freq='1min',
    mixed_types=False,
):
    """
    Generate test DataFrames with configurable properties.

    Args:
        rows: Number of rows
        num_fields: Number of numeric field columns
        num_tags: Number of tag columns
        with_nans: Include NaN values
        nan_percentage: Percentage of NaN values if with_nans=True
        start_time: Start datetime, defaults to 2024-01-01
        freq: Frequency string for date range
        mixed_types: Include mixed data types
    """
    if start_time is None:
        start_time = '2024-01-01'

    time_index = pd.date_range(start=start_time, periods=rows, freq=freq)

    data = {}

    for i in range(num_fields):
        values = np.random.randn(rows) * 100
        if with_nans:
            nan_indices = np.random.choice(rows, int(rows * nan_percentage), replace=False)
            values[nan_indices] = np.nan
        data[f'field_{i+1}'] = values

    for i in range(num_tags):
        data[f'tag_{i+1}'] = [f'value_{j % 5}' for j in range(rows)]

    if mixed_types:
        data['int_field'] = np.random.randint(0, 100, rows)
        data['bool_field'] = np.random.choice([True, False], rows)
        data['str_field'] = [f'string_{i}' for i in range(rows)]

    df = pd.DataFrame(data, index=time_index)
    return df


def create_mock_error_scenarios():
    """
    Create mock error scenarios for testing error handling.
    """
    from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError
    from requests.exceptions import ConnectionError, Timeout

    return {
        'connection_error': ConnectionError("Connection refused"),
        'timeout': Timeout("Request timeout"),
        'client_error_400': InfluxDBClientError("Bad request", code=400),
        'client_error_401': InfluxDBClientError("Unauthorized", code=401),
        'client_error_404': InfluxDBClientError("Not found", code=404),
        'server_error_500': InfluxDBServerError("Internal server error"),
        'server_error_503': InfluxDBServerError("Service unavailable"),
    }


def create_database_list_response(db_names=None):
    """Create mock response for get_list_database()."""
    if db_names is None:
        db_names = ['_internal', 'test_db', 'production']
    return [{'name': name} for name in db_names]


def create_measurements_list_response(measurement_names=None):
    """Create mock response for SHOW MEASUREMENTS query."""
    if measurement_names is None:
        measurement_names = ['cpu', 'memory', 'disk', 'network']

    mock_result = MagicMock()
    mock_result.raw = {
        'series': [{
            'name': 'measurements',
            'columns': ['name'],
            'values': [[name] for name in measurement_names]
        }]
    }

    points = [{'name': name} for name in measurement_names]
    mock_result.get_points.return_value = iter(points)

    return mock_result


def create_tag_keys_response(tag_keys=None):
    """Create mock response for SHOW TAG KEYS query."""
    if tag_keys is None:
        tag_keys = ['host', 'region', 'datacenter']

    mock_result = MagicMock()
    mock_result.raw = {
        'series': [{
            'name': 'cpu',
            'columns': ['tagKey'],
            'values': [[key] for key in tag_keys]
        }]
    }

    points = [{'tagKey': key} for key in tag_keys]
    mock_result.get_points.return_value = iter(points)

    return mock_result


def create_field_keys_response(field_keys=None):
    """Create mock response for SHOW FIELD KEYS query."""
    if field_keys is None:
        field_keys = [
            ('usage_user', 'float'),
            ('usage_system', 'float'),
            ('usage_idle', 'float'),
            ('count', 'integer'),
        ]

    mock_result = MagicMock()
    mock_result.raw = {
        'series': [{
            'name': 'cpu',
            'columns': ['fieldKey', 'fieldType'],
            'values': list(field_keys)
        }]
    }

    points = [{'fieldKey': k, 'fieldType': t} for k, t in field_keys]
    mock_result.get_points.return_value = iter(points)

    return mock_result


def create_retention_policies_response(policies=None):
    """Create mock response for SHOW RETENTION POLICIES query."""
    if policies is None:
        policies = [
            {'name': 'autogen', 'duration': '0s', 'shardGroupDuration': '168h0m0s',
             'replicaN': 1, 'default': True},
            {'name': 'one_day', 'duration': '24h0m0s', 'shardGroupDuration': '1h0m0s',
             'replicaN': 1, 'default': False},
        ]

    mock_result = MagicMock()
    columns = ['name', 'duration', 'shardGroupDuration', 'replicaN', 'default']
    values = [[p['name'], p['duration'], p['shardGroupDuration'], p['replicaN'], p['default']]
              for p in policies]

    mock_result.raw = {
        'series': [{
            'columns': columns,
            'values': values
        }]
    }

    mock_result.get_points.return_value = iter(policies)

    return mock_result


def create_continuous_queries_response(queries=None):
    """Create mock response for SHOW CONTINUOUS QUERIES."""
    if queries is None:
        queries = [
            {'name': 'cq_30m', 'query': 'CREATE CONTINUOUS QUERY cq_30m ON test_db BEGIN SELECT mean(value) INTO mean_30m FROM data GROUP BY time(30m) END'},
        ]

    mock_result = MagicMock()
    mock_result.raw = {
        'series': [{
            'name': 'test_db',
            'columns': ['name', 'query'],
            'values': [[q['name'], q['query']] for q in queries]
        }]
    }

    mock_result.get_points.return_value = iter(queries)

    return mock_result
