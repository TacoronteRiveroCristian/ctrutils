import json
import logging
from typing import List, Dict, Any
from datetime import datetime

from .validator import DatabaseComparison

logger = logging.getLogger(__name__)


class StatisticsReporter:
    """Generates comprehensive comparison reports"""

    def __init__(self, comparisons: List[DatabaseComparison]):
        self.comparisons = comparisons

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive statistics report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'summary': self._generate_summary(),
            'databases': self._generate_database_stats(),
            'measurements': self._generate_measurement_stats(),
            'integrity': self._generate_integrity_stats()
        }

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate high-level summary"""
        total_measurements = sum(
            len(db.measurement_comparisons) for db in self.comparisons
        )
        matching_measurements = sum(
            sum(1 for m in db.measurement_comparisons if m.match)
            for db in self.comparisons
        )

        total_source_points = sum(
            db.summary['total_source_points'] for db in self.comparisons
        )
        total_dest_points = sum(
            db.summary['total_dest_points'] for db in self.comparisons
        )

        return {
            'total_databases': len(self.comparisons),
            'total_measurements': total_measurements,
            'matching_measurements': matching_measurements,
            'match_percentage': (
                matching_measurements / total_measurements * 100
                if total_measurements > 0 else 0
            ),
            'total_points_source': total_source_points,
            'total_points_dest': total_dest_points,
            'total_difference': abs(total_source_points - total_dest_points)
        }

    def _generate_database_stats(self) -> List[Dict[str, Any]]:
        """Generate per-database statistics"""
        stats = []
        for db_comp in self.comparisons:
            stats.append({
                'name': db_comp.database,
                'measurement_count': len(db_comp.measurement_comparisons),
                'total_points': db_comp.summary['total_source_points'],
                'integrity_pass': all(
                    m.match for m in db_comp.measurement_comparisons
                ),
                'match_percentage': db_comp.summary['match_percentage']
            })
        return stats

    def _generate_measurement_stats(self) -> List[Dict[str, Any]]:
        """Generate per-measurement statistics"""
        stats = []
        for db_comp in self.comparisons:
            for m_comp in db_comp.measurement_comparisons:
                stats.append({
                    'database': db_comp.database,
                    'measurement': m_comp.measurement,
                    'source_count': m_comp.source_count,
                    'dest_count': m_comp.dest_count,
                    'match': m_comp.match,
                    'difference': m_comp.difference,
                    'diff_percentage': m_comp.difference_percentage
                })
        return stats

    def _generate_integrity_stats(self) -> Dict[str, Any]:
        """Generate integrity check results"""
        failed_measurements = []
        for db_comp in self.comparisons:
            for m_comp in db_comp.measurement_comparisons:
                if not m_comp.match:
                    failed_measurements.append({
                        'database': db_comp.database,
                        'measurement': m_comp.measurement,
                        'difference': m_comp.difference
                    })

        return {
            'passed': len(failed_measurements) == 0,
            'failed_measurements': failed_measurements,
            'failure_count': len(failed_measurements)
        }

    def print_report(self):
        """Print formatted report to console"""
        report = self.generate_report()

        print("\n" + "=" * 80)
        print("INFLUXDB BACKUP/RESTORE TEST REPORT")
        print("=" * 80)
        print(f"Timestamp: {report['timestamp']}")

        # Summary section
        summary = report['summary']
        print("\nSUMMARY:")
        print(f"  Total Databases:       {summary['total_databases']}")
        print(f"  Total Measurements:    {summary['total_measurements']}")
        print(f"  Matching Measurements: {summary['matching_measurements']}")
        print(f"  Match Percentage:      {summary['match_percentage']:.2f}%")
        print(f"  Total Points (Source): {summary['total_points_source']:,}")
        print(f"  Total Points (Dest):   {summary['total_points_dest']:,}")
        print(f"  Total Difference:      {summary['total_difference']:,}")

        # Per-database stats
        print("\nDATABASE STATISTICS:")
        for db_stats in report['databases']:
            status = "PASS" if db_stats['integrity_pass'] else "FAIL"
            print(f"\n  {db_stats['name']}:")
            print(f"    Measurements:   {db_stats['measurement_count']}")
            print(f"    Total Points:   {db_stats['total_points']:,}")
            print(f"    Match Rate:     {db_stats['match_percentage']:.2f}%")
            print(f"    Integrity:      {status}")

        # Measurement details
        print("\nMEASUREMENT COMPARISON:")
        for m in report['measurements']:
            status = "OK" if m['match'] else "XX"
            print(
                f"  [{status}] {m['database']}.{m['measurement']}: "
                f"Source={m['source_count']:,} | Dest={m['dest_count']:,}"
            )
            if not m['match']:
                print(f"       Difference: {m['difference']:,} ({m['diff_percentage']:.2f}%)")

        # Integrity summary
        integrity = report['integrity']
        print("\nINTEGRITY CHECK:")
        if integrity['passed']:
            print("  Status: PASSED - All measurements match within tolerance")
        else:
            print(f"  Status: FAILED - {integrity['failure_count']} measurement(s) mismatch")
            for failed in integrity['failed_measurements']:
                print(f"    - {failed['database']}.{failed['measurement']}: {failed['difference']} point difference")

        print("\n" + "=" * 80 + "\n")

    def save_report(self, filename: str):
        """Save report to JSON file"""
        report = self.generate_report()
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved to: {filename}")
