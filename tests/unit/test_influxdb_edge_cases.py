import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
import pytest

import sys
sys.path.insert(0, '/home/cristiantr/GitHub/ctrutils')

from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from tests.fixtures.influxdb_fixtures import (
    create_mock_influxdb_client,
)


@pytest.mark.unit
@pytest.mark.edge_case
class TestInfluxdbConnectionEdgeCases(unittest.TestCase):

    def test_init_without_client_or_host_port(self):
        with self.assertRaises(ValueError):
            InfluxdbOperation()


@pytest.mark.unit
@pytest.mark.edge_case
class TestInfluxdbDataNormalizationEdgeCases(unittest.TestCase):

    def setUp(self):
        mock_client = create_mock_influxdb_client()
        self.influx_op = InfluxdbOperation(client=mock_client, database='test_db')

    def test_normalize_positive_infinity(self):
        value = float('inf')
        normalized = self.influx_op.normalize_value_to_write(value)
        self.assertIsNone(normalized)

    def test_normalize_negative_infinity(self):
        value = float('-inf')
        normalized = self.influx_op.normalize_value_to_write(value)
        self.assertIsNone(normalized)

    def test_normalize_numpy_nan(self):
        value = np.nan
        normalized = self.influx_op.normalize_value_to_write(value)
        self.assertIsNone(normalized)

    def test_normalize_pandas_na(self):
        value = pd.NA
        normalized = self.influx_op.normalize_value_to_write(value)
        self.assertIsNone(normalized)

    def test_normalize_none(self):
        value = None
        normalized = self.influx_op.normalize_value_to_write(value)
        self.assertIsNone(normalized)

    def test_normalize_very_large_positive_number(self):
        value = 1e308
        normalized = self.influx_op.normalize_value_to_write(value)
        self.assertEqual(normalized, value)

    def test_normalize_very_large_negative_number(self):
        value = -1e308
        normalized = self.influx_op.normalize_value_to_write(value)
        self.assertEqual(normalized, value)

    def test_normalize_unicode_string(self):
        test_cases = ['北京', 'Москва', 'café', '🌡️']
        for value in test_cases:
            normalized = self.influx_op.normalize_value_to_write(value)
            self.assertEqual(normalized, value)

    def test_normalize_empty_string_becomes_none(self):
        value = ''
        normalized = self.influx_op.normalize_value_to_write(value)
        self.assertIsNone(normalized)

    def test_normalize_whitespace_string_becomes_none(self):
        value = '   '
        normalized = self.influx_op.normalize_value_to_write(value)
        self.assertIsNone(normalized)

    def test_normalize_numpy_int_types(self):
        test_cases = [
            (np.int8(10), 10.0),
            (np.int16(100), 100.0),
            (np.int32(1000), 1000.0),
            (np.int64(10000), 10000.0),
        ]
        for value, expected in test_cases:
            normalized = self.influx_op.normalize_value_to_write(value)
            self.assertEqual(normalized, expected)


if __name__ == '__main__':
    unittest.main()
