import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from ctrutils.database.influxdb import InfluxdbOperation

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages backup and restore operations between InfluxDB instances"""

    def __init__(
        self,
        source_op: InfluxdbOperation,
        dest_op: InfluxdbOperation,
        backup_dir: str = '/app/backup_data'
    ):
        self.source = source_op
        self.dest = dest_op
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"BackupManager initialized with backup_dir: {self.backup_dir}")

    def backup_database(
        self,
        database: str,
        include_timestamp: bool = True
    ) -> Dict[str, Any]:
        """
        Backup entire database (all measurements) to CSV files

        Returns dict with backup metadata and results
        """
        logger.info(f"Starting backup of database: {database}")

        measurements = self.source.list_measurements(database)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        results = {
            'database': database,
            'timestamp': timestamp,
            'measurements': {},
            'total_points': 0,
            'errors': []
        }

        for measurement in measurements:
            try:
                filename = f"{database}_{measurement}_{timestamp}.csv"
                output_file = str(self.backup_dir / filename)

                logger.info(f"Backing up {measurement} to {filename}")

                points_exported = self.source.backup_measurement(
                    measurement=measurement,
                    output_file=output_file,
                    database=database
                )

                results['measurements'][measurement] = {
                    'file': filename,
                    'points': points_exported
                }
                results['total_points'] += points_exported

                logger.info(f"Successfully backed up {measurement}: {points_exported} points")

            except Exception as e:
                error_msg = f"Error backing up {measurement}: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)

        logger.info(
            f"Database {database} backup complete: "
            f"{len(measurements)} measurements, {results['total_points']} total points"
        )

        return results

    def restore_database(
        self,
        backup_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Restore database from backup files

        Args:
            backup_results: Results dict from backup_database()
        """
        database = backup_results['database']
        logger.info(f"Starting restore of database: {database}")

        # Create database on destination if it doesn't exist
        existing_dbs = self.dest.list_databases()
        if database not in existing_dbs:
            logger.info(f"Creating database: {database}")
            self.dest.create_database(database)

        results = {
            'database': database,
            'measurements': {},
            'total_points': 0,
            'errors': []
        }

        for measurement, info in backup_results['measurements'].items():
            try:
                input_file = str(self.backup_dir / info['file'])
                logger.info(f"Restoring {measurement} from {info['file']}")

                stats = self.dest.restore_measurement(
                    measurement=measurement,
                    input_file=input_file,
                    database=database,
                    batch_size=5000
                )

                results['measurements'][measurement] = stats
                results['total_points'] += stats['successful']

                logger.info(
                    f"Successfully restored {measurement}: "
                    f"{stats['successful']} points"
                )

            except Exception as e:
                error_msg = f"Error restoring {measurement}: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)

        logger.info(
            f"Database {database} restore complete: "
            f"{len(results['measurements'])} measurements, "
            f"{results['total_points']} total points"
        )

        return results

    def backup_all_databases(
        self,
        databases: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Backup multiple databases"""
        results = {}
        for database in databases:
            results[database] = self.backup_database(database)
        return results

    def restore_all_databases(
        self,
        backup_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Restore multiple databases"""
        results = {}
        for database, backup_info in backup_results.items():
            results[database] = self.restore_database(backup_info)
        return results
