import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
import math
from datetime import datetime
import pytz
import pytest

import sys
sys.path.insert(0, '/home/cristiantr/GitHub/ctrutils')

from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from tests.fixtures.influxdb_fixtures import (
    create_mock_influxdb_client,
)


@pytest.mark.unit
@pytest.mark.edge_case
class TestNormalizeValueToWrite(unittest.TestCase):
    def setUp(self):
        mock_client = create_mock_influxdb_client()
        self.influx_op = InfluxdbOperation(client=mock_client, database='test_db')

    def test_normalize_none_value(self):
        self.assertIsNone(self.influx_op.normalize_value_to_write(None))

    def test_normalize_numpy_nan(self):
        self.assertIsNone(self.influx_op.normalize_value_to_write(np.nan))

    def test_normalize_pandas_na(self):
        self.assertIsNone(self.influx_op.normalize_value_to_write(pd.NA))

    def test_normalize_math_nan(self):
        self.assertIsNone(self.influx_op.normalize_value_to_write(math.nan))

    def test_normalize_positive_infinity(self):
        self.assertIsNone(self.influx_op.normalize_value_to_write(float('inf')))

    def test_normalize_negative_infinity(self):
        self.assertIsNone(self.influx_op.normalize_value_to_write(float('-inf')))

    def test_normalize_python_int(self):
        self.assertEqual(self.influx_op.normalize_value_to_write(42), 42)

    def test_normalize_python_float(self):
        self.assertEqual(self.influx_op.normalize_value_to_write(3.14), 3.14)

    def test_normalize_python_string(self):
        self.assertEqual(self.influx_op.normalize_value_to_write("test"), "test")

    def test_normalize_empty_string_becomes_none(self):
        result = self.influx_op.normalize_value_to_write("")
        self.assertIsNone(result)

    def test_normalize_whitespace_string_becomes_none(self):
        result = self.influx_op.normalize_value_to_write("   ")
        self.assertIsNone(result)

    def test_normalize_boolean_true(self):
        self.assertEqual(self.influx_op.normalize_value_to_write(True), True)

    def test_normalize_boolean_false(self):
        self.assertEqual(self.influx_op.normalize_value_to_write(False), False)

    def test_normalize_numpy_int8(self):
        result = self.influx_op.normalize_value_to_write(np.int8(10))
        self.assertEqual(result, 10)

    def test_normalize_numpy_int16(self):
        result = self.influx_op.normalize_value_to_write(np.int16(100))
        self.assertEqual(result, 100)

    def test_normalize_numpy_int32(self):
        result = self.influx_op.normalize_value_to_write(np.int32(1000))
        self.assertEqual(result, 1000)

    def test_normalize_numpy_int64(self):
        result = self.influx_op.normalize_value_to_write(np.int64(10000))
        self.assertEqual(result, 10000)

    def test_normalize_numpy_float32(self):
        result = self.influx_op.normalize_value_to_write(np.float32(1.5))
        self.assertAlmostEqual(result, 1.5, places=5)

    def test_normalize_numpy_float64(self):
        result = self.influx_op.normalize_value_to_write(np.float64(2.5))
        self.assertEqual(result, 2.5)

    def test_normalize_numpy_bool_true(self):
        result = self.influx_op.normalize_value_to_write(np.bool_(True))
        self.assertEqual(result, True)

    def test_normalize_numpy_bool_false(self):
        result = self.influx_op.normalize_value_to_write(np.bool_(False))
        self.assertEqual(result, False)

    def test_normalize_very_large_positive_number(self):
        value = 1e308
        self.assertEqual(self.influx_op.normalize_value_to_write(value), value)

    def test_normalize_very_small_positive_number(self):
        value = 1e-308
        self.assertEqual(self.influx_op.normalize_value_to_write(value), value)

    def test_normalize_zero_float(self):
        self.assertEqual(self.influx_op.normalize_value_to_write(0.0), 0.0)

    def test_normalize_unicode_chinese(self):
        value = '北京'
        self.assertEqual(self.influx_op.normalize_value_to_write(value), value)

    def test_normalize_unicode_cyrillic(self):
        value = 'Москва'
        self.assertEqual(self.influx_op.normalize_value_to_write(value), value)

    def test_normalize_unicode_accented(self):
        value = 'café'
        self.assertEqual(self.influx_op.normalize_value_to_write(value), value)

    def test_normalize_unicode_emoji(self):
        value = '🌡️'
        self.assertEqual(self.influx_op.normalize_value_to_write(value), value)


@pytest.mark.unit
@pytest.mark.edge_case
class TestValidatePoint(unittest.TestCase):

    def setUp(self):
        mock_client = create_mock_influxdb_client()
        self.influx_op = InfluxdbOperation(client=mock_client, database='test_db')

    def test_validate_point_with_valid_data(self):
        point = {
            "measurement": "test",
            "tags": {"location": "lab"},
            "time": "2024-01-01T12:00:00Z",
            "fields": {"value": 1.0}
        }
        result = self.influx_op._validate_point(point)
        self.assertTrue(result)

    def test_validate_point_with_all_nan_fields(self):
        point = {
            "measurement": "test",
            "tags": {"location": "lab"},
            "time": "2024-01-01T12:00:00Z",
            "fields": {"value1": np.nan, "value2": None}
        }
        result = self.influx_op._validate_point(point)
        self.assertFalse(result)

    def test_validate_point_with_mixed_valid_invalid_fields(self):
        point = {
            "measurement": "test",
            "tags": {"location": "lab"},
            "time": "2024-01-01T12:00:00Z",
            "fields": {"value1": 1.0, "value2": np.nan, "value3": None, "value4": 2.0}
        }
        result = self.influx_op._validate_point(point)
        self.assertTrue(result)

    def test_validate_point_with_empty_fields(self):
        point = {
            "measurement": "test",
            "tags": {"location": "lab"},
            "time": "2024-01-01T12:00:00Z",
            "fields": {}
        }
        result = self.influx_op._validate_point(point)
        self.assertFalse(result)

    def test_validate_point_with_infinity_values(self):
        point = {
            "measurement": "test",
            "tags": {"location": "lab"},
            "time": "2024-01-01T12:00:00Z",
            "fields": {"value1": float('inf'), "value2": float('-inf')}
        }
        result = self.influx_op._validate_point(point)
        self.assertFalse(result)

    def test_validate_point_with_only_one_valid_field(self):
        point = {
            "measurement": "test",
            "tags": {"location": "lab"},
            "time": "2024-01-01T12:00:00Z",
            "fields": {"value": 1.0, "invalid1": np.nan, "invalid2": None}
        }
        result = self.influx_op._validate_point(point)
        self.assertTrue(result)


@pytest.mark.unit
@pytest.mark.edge_case
class TestConvertToUtcIso(unittest.TestCase):

    def setUp(self):
        mock_client = create_mock_influxdb_client()
        self.influx_op = InfluxdbOperation(client=mock_client, database='test_db')

    def test_convert_naive_datetime(self):
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = self.influx_op._convert_to_utc_iso(dt)
        self.assertIsInstance(result, str)
        self.assertIn('2024-01-01', result)

    def test_convert_timezone_aware_datetime(self):
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        result = self.influx_op._convert_to_utc_iso(dt)
        self.assertIsInstance(result, str)
        self.assertIn('2024-01-01', result)

    def test_convert_non_utc_timezone_datetime(self):
        eastern = pytz.timezone('America/New_York')
        dt = eastern.localize(datetime(2024, 1, 1, 12, 0, 0))
        result = self.influx_op._convert_to_utc_iso(dt)
        self.assertIsInstance(result, str)

    def test_convert_pandas_timestamp_naive(self):
        ts = pd.Timestamp('2024-01-01 12:00:00')
        result = self.influx_op._convert_to_utc_iso(ts)
        self.assertIsInstance(result, str)
        self.assertIn('2024-01-01', result)

    def test_convert_pandas_timestamp_utc(self):
        ts = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        result = self.influx_op._convert_to_utc_iso(ts)
        self.assertIsInstance(result, str)
        self.assertIn('2024-01-01', result)

    def test_convert_pandas_timestamp_with_timezone(self):
        ts = pd.Timestamp('2024-01-01 12:00:00', tz='America/New_York')
        result = self.influx_op._convert_to_utc_iso(ts)
        self.assertIsInstance(result, str)

    def test_convert_string_passthrough(self):
        iso_string = '2024-01-01T12:00:00Z'
        result = self.influx_op._convert_to_utc_iso(iso_string)
        self.assertEqual(result, iso_string)


if __name__ == '__main__':
    unittest.main()
