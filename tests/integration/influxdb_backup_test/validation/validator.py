import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from ctrutils.database.influxdb import InfluxdbOperation

logger = logging.getLogger(__name__)


@dataclass
class MeasurementComparison:
    """Comparison results for a single measurement"""
    measurement: str
    source_count: int
    dest_count: int
    match: bool
    difference: int
    difference_percentage: float


@dataclass
class DatabaseComparison:
    """Comparison results for a database"""
    database: str
    source_measurements: List[str]
    dest_measurements: List[str]
    measurements_match: bool
    measurement_comparisons: List[MeasurementComparison]
    summary: Dict[str, Any]


class DataValidator:
    """Validates data integrity between source and destination InfluxDB instances"""

    def __init__(
        self,
        source_op: InfluxdbOperation,
        dest_op: InfluxdbOperation,
        tolerance: float = 0.01
    ):
        self.source = source_op
        self.dest = dest_op
        self.tolerance = tolerance  # Percentage tolerance for comparisons
        logger.info(f"DataValidator initialized with tolerance: {tolerance}%")

    def compare_databases(
        self,
        databases: List[str],
        detailed: bool = False
    ) -> List[DatabaseComparison]:
        """Compare multiple databases"""
        results = []
        for database in databases:
            comparison = self.compare_database(database, detailed=detailed)
            results.append(comparison)
        return results

    def compare_database(
        self,
        database: str,
        detailed: bool = False
    ) -> DatabaseComparison:
        """Compare single database structure and data"""
        logger.info(f"Comparing database: {database}")

        source_measurements = self.source.list_measurements(database)
        dest_measurements = self.dest.list_measurements(database)

        measurements_match = set(source_measurements) == set(dest_measurements)

        if not measurements_match:
            logger.warning(
                f"Measurement lists don't match for {database}: "
                f"source={len(source_measurements)}, dest={len(dest_measurements)}"
            )

        measurement_comparisons = []
        for measurement in source_measurements:
            if measurement in dest_measurements:
                comp = self.compare_measurement(
                    database,
                    measurement,
                    detailed=detailed
                )
                measurement_comparisons.append(comp)
            else:
                logger.warning(f"Measurement {measurement} missing from destination")

        summary = self._create_summary(measurement_comparisons)

        logger.info(
            f"Database {database} comparison complete: "
            f"{summary['total_measurements']} measurements, "
            f"{summary['matching_measurements']} matches"
        )

        return DatabaseComparison(
            database=database,
            source_measurements=source_measurements,
            dest_measurements=dest_measurements,
            measurements_match=measurements_match,
            measurement_comparisons=measurement_comparisons,
            summary=summary
        )

    def compare_measurement(
        self,
        database: str,
        measurement: str,
        detailed: bool = False
    ) -> MeasurementComparison:
        """Compare single measurement point counts"""
        logger.debug(f"Comparing measurement: {database}.{measurement}")

        # Count points
        source_count = self.source.count_points(measurement, database)
        dest_count = self.dest.count_points(measurement, database)

        difference = abs(source_count - dest_count)
        diff_pct = (difference / source_count * 100) if source_count > 0 else 0
        match = difference <= (source_count * self.tolerance / 100)

        if not match:
            logger.warning(
                f"Measurement {measurement} mismatch: "
                f"source={source_count}, dest={dest_count}, diff={difference}"
            )

        return MeasurementComparison(
            measurement=measurement,
            source_count=source_count,
            dest_count=dest_count,
            match=match,
            difference=difference,
            difference_percentage=diff_pct
        )

    def _create_summary(
        self,
        comparisons: List[MeasurementComparison]
    ) -> Dict[str, Any]:
        """Create summary statistics from measurement comparisons"""
        total = len(comparisons)
        matching = sum(1 for c in comparisons if c.match)

        total_source_points = sum(c.source_count for c in comparisons)
        total_dest_points = sum(c.dest_count for c in comparisons)

        return {
            'total_measurements': total,
            'matching_measurements': matching,
            'match_percentage': (matching / total * 100) if total > 0 else 0,
            'total_source_points': total_source_points,
            'total_dest_points': total_dest_points,
            'total_difference': abs(total_source_points - total_dest_points)
        }
