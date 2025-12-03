"""Tests for write operations in InfluxdbOperation."""
import unittest
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np

from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from tests.fixtures.influxdb_fixtures import create_mock_influxdb_client, create_test_dataframe


@pytest.mark.unit
class TestWriteDataframeParameterCombinations(unittest.TestCase):
    """Test write_dataframe with different parameter combinations to increase branch coverage."""

    def setUp(self):
        self.mock_client = create_mock_influxdb_client(write_points_return=True)
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_write_dataframe_drop_na_rows_true(self):
        """Test drop_na_rows=True parameter."""
        df = pd.DataFrame({
            'field1': [1.0, np.nan, 3.0],
            'field2': [np.nan, np.nan, 6.0],
        }, index=pd.date_range('2024-01-01', periods=3, freq='1min'))

        self.influx.write_dataframe(measurement='test', data=df, drop_na_rows=True)
        self.assertTrue(self.mock_client.write_points.called)

    def test_write_dataframe_convert_bool_to_float_true(self):
        """Test convert_bool_to_float=True parameter."""
        df = pd.DataFrame({
            'bool_field': [True, False, True],
            'value': [1.0, 2.0, 3.0],
        }, index=pd.date_range('2024-01-01', periods=3, freq='1min'))

        self.influx.write_dataframe(measurement='test', data=df, convert_bool_to_float=True)
        self.assertTrue(self.mock_client.write_points.called)

    def test_write_dataframe_convert_bool_custom_suffix(self):
        """Test convert_bool_to_float with custom suffix."""
        df = pd.DataFrame({
            'active': [True, False],
        }, index=pd.date_range('2024-01-01', periods=2, freq='1min'))

        self.influx.write_dataframe(
            measurement='test',
            data=df,
            convert_bool_to_float=True,
            suffix_bool_to_float='_int'
        )
        self.assertTrue(self.mock_client.write_points.called)

    def test_write_dataframe_pass_to_float_true(self):
        """Test pass_to_float=True parameter."""
        df = pd.DataFrame({
            'int_val': [1, 2, 3],
        }, index=pd.date_range('2024-01-01', periods=3, freq='1min'))

        self.influx.write_dataframe(
            measurement='test',
            data=df,
            pass_to_float=True,
            validate_data=False
        )
        self.assertTrue(self.mock_client.write_points.called)

    def test_write_dataframe_pass_to_float_false(self):
        """Test pass_to_float=False parameter."""
        df = pd.DataFrame({
            'int_val': [1, 2, 3],
        }, index=pd.date_range('2024-01-01', periods=3, freq='1min'))

        self.influx.write_dataframe(
            measurement='test',
            data=df,
            pass_to_float=False,
            validate_data=False
        )
        self.assertTrue(self.mock_client.write_points.called)

    def test_write_dataframe_empty(self):
        """Test with empty DataFrame raises error."""
        df = pd.DataFrame({'field1': []}, index=pd.DatetimeIndex([]))

        with pytest.raises(ValueError, match="La lista de puntos no puede estar vacia"):
            self.influx.write_dataframe(measurement='test', data=df)

    def test_write_dataframe_single_row(self):
        """Test with single row DataFrame."""
        df = pd.DataFrame({'field1': [42.0]}, index=pd.date_range('2024-01-01', periods=1))

        result = self.influx.write_dataframe(measurement='test', data=df)
        self.assertTrue(self.mock_client.write_points.called)

    def test_write_dataframe_raises_on_none_data(self):
        """Test raises ValueError when data is None."""
        with pytest.raises(ValueError, match="Debe proporcionar un DataFrame"):
            self.influx.write_dataframe(measurement='test', data=None)

    def test_write_dataframe_raises_on_none_measurement(self):
        """Test raises ValueError when measurement is None."""
        df = create_test_dataframe(rows=3)
        with pytest.raises(ValueError, match="Debe proporcionar un DataFrame"):
            self.influx.write_dataframe(measurement=None, data=df)

    def test_write_dataframe_raises_on_non_datetime_index(self):
        """Test raises TypeError when index is not DatetimeIndex."""
        df = pd.DataFrame({'field1': [1.0, 2.0]}, index=[0, 1])

        with pytest.raises(TypeError, match="debe ser de tipo DatetimeIndex"):
            self.influx.write_dataframe(measurement='test', data=df)


@pytest.mark.unit
class TestWritePointsBatchingAndStats(unittest.TestCase):
    """Test write_points batching and statistics."""

    def setUp(self):
        self.mock_client = create_mock_influxdb_client(write_points_return=True)
        self.influx = InfluxdbOperation(client=self.mock_client)
        self.influx._database = 'test_db'

    def test_write_points_different_batch_sizes(self):
        """Test write_points with different batch sizes."""
        points = [{'measurement': 'test', 'time': f'2024-01-01T12:{i:02d}:00Z', 'fields': {'value': i}}
                  for i in range(50)]

        for batch_size in [1, 10, 50]:
            self.mock_client.reset_mock()
            result = self.influx.write_points(points=points, batch_size=batch_size)
            self.assertEqual(result['total_points'], 50)

    def test_write_points_empty_list(self):
        """Test write_points with empty list raises error."""
        with pytest.raises(ValueError, match="La lista de puntos no puede estar vacia"):
            self.influx.write_points(points=[])

    def test_write_points_stats_structure(self):
        """Test write_points returns correct stats."""
        points = [{'measurement': 'test', 'time': '2024-01-01T12:00:00Z', 'fields': {'value': i}}
                  for i in range(10)]

        result = self.influx.write_points(points=points, batch_size=5)

        self.assertIn('total_points', result)
        self.assertIn('written_points', result)
        self.assertIn('invalid_points', result)
        self.assertIn('batches', result)
        self.assertEqual(result['total_points'], 10)
        self.assertEqual(result['batches'], 2)

    def test_write_points_with_global_tags(self):
        """Test write_points with global tags."""
        points = [{'measurement': 'test', 'time': '2024-01-01T12:00:00Z', 'fields': {'value': 1.0}}]

        self.influx.write_points(points=points, tags={'location': 'lab'})
        self.assertTrue(self.mock_client.write_points.called)
