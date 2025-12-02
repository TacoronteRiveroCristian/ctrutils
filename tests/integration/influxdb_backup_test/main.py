import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, List

from ctrutils.database.influxdb import InfluxdbOperation

from generator.data_generator import HeterogeneousDataGenerator
from backup.backup_manager import BackupManager
from validation.validator import DataValidator
from validation.statistics import StatisticsReporter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/logs/backup_test.log')
    ]
)
logger = logging.getLogger(__name__)


class BackupTestOrchestrator:
    """Orchestrates the complete backup/restore testing workflow"""

    def __init__(self):
        self.config = self._load_config()
        self._setup_influxdb_connections()
        self._setup_components()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        return {
            'source': {
                'host': os.getenv('SOURCE_HOST', 'influxdb-source'),
                'port': int(os.getenv('SOURCE_PORT', 8086))
            },
            'dest': {
                'host': os.getenv('DEST_HOST', 'influxdb-destination'),
                'port': int(os.getenv('DEST_PORT', 8086))
            },
            'influxdb': {
                'user': os.getenv('INFLUXDB_USER', 'admin'),
                'password': os.getenv('INFLUXDB_PASSWORD', 'admin123')
            },
            'test': {
                'initial_hours': int(os.getenv('INITIAL_HOURS', 2)),
                'continuous_generation': os.getenv('CONTINUOUS_GENERATION', 'false').lower() == 'true',
                'test_duration': int(os.getenv('TEST_DURATION', 300)),
                'generation_interval': int(os.getenv('GENERATION_INTERVAL', 10))
            }
        }

    def _setup_influxdb_connections(self):
        """Initialize InfluxDB connections"""
        logger.info("Connecting to source InfluxDB...")
        self.source_op = InfluxdbOperation(
            host=self.config['source']['host'],
            port=self.config['source']['port'],
            username=self.config['influxdb']['user'],
            password=self.config['influxdb']['password']
        )
        self.source_op.enable_logging(level=logging.INFO)

        logger.info("Connecting to destination InfluxDB...")
        self.dest_op = InfluxdbOperation(
            host=self.config['dest']['host'],
            port=self.config['dest']['port'],
            username=self.config['influxdb']['user'],
            password=self.config['influxdb']['password']
        )
        self.dest_op.enable_logging(level=logging.INFO)

        # Test connections
        try:
            self.source_op.list_databases()
            self.dest_op.list_databases()
            logger.info("Successfully connected to both InfluxDB instances")
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            raise

    def _setup_components(self):
        """Initialize test components"""
        self.generator = HeterogeneousDataGenerator()
        self.backup_manager = BackupManager(self.source_op, self.dest_op)
        self.validator = DataValidator(self.source_op, self.dest_op)

    def run_test(self) -> bool:
        """
        Execute complete test workflow

        Returns:
            True if test passed, False otherwise
        """
        logger.info("=" * 80)
        logger.info("STARTING INFLUXDB BACKUP/RESTORE TEST")
        logger.info("=" * 80)

        try:
            # Phase 1: Generate initial bulk data
            logger.info("\n[PHASE 1] Generating initial bulk data...")
            self._phase1_generate_bulk_data()

            # Phase 2: Backup all databases
            logger.info("\n[PHASE 2] Backing up all databases...")
            backup_results = self._phase2_backup()

            # Phase 3: Restore to destination
            logger.info("\n[PHASE 3] Restoring to destination...")
            restore_results = self._phase3_restore(backup_results)

            # Phase 4: Validate data integrity
            logger.info("\n[PHASE 4] Validating data integrity...")
            comparisons = self._phase4_validate()

            # Phase 5: Real-time data generation (optional)
            if self.config['test'].get('continuous_generation', False):
                logger.info("\n[PHASE 5] Continuous data generation...")
                self._phase5_continuous_generation()

            # Generate and print report
            logger.info("\n[REPORT] Generating test report...")
            reporter = StatisticsReporter(comparisons)
            reporter.print_report()
            reporter.save_report('/app/logs/test_report.json')

            # Determine test result
            passed = all(db.summary['match_percentage'] == 100.0 for db in comparisons)

            if passed:
                logger.info("\n" + "=" * 80)
                logger.info("TEST PASSED - All data backed up and restored successfully")
                logger.info("=" * 80)
            else:
                logger.error("\n" + "=" * 80)
                logger.error("TEST FAILED - Data mismatches detected")
                logger.error("=" * 80)

            return passed

        except Exception as e:
            logger.error(f"Test failed with exception: {e}", exc_info=True)
            return False

    def _phase1_generate_bulk_data(self):
        """Generate initial data for all databases"""
        start_time = time.time()

        for db_schema in self.generator.schemas:
            logger.info(f"Creating database: {db_schema.name}")
            self.source_op.create_database(db_schema.name)

            # Generate data for each measurement
            bulk_data = self.generator.generate_bulk_data(
                db_schema,
                hours=self.config['test']['initial_hours']
            )

            for measurement, df in bulk_data.items():
                logger.info(
                    f"Writing {len(df)} points to {db_schema.name}.{measurement}"
                )

                # Extract tags from DataFrame metadata
                tags = getattr(df, '_tags', {})

                stats = self.source_op.write_dataframe(
                    measurement=measurement,
                    data=df,
                    tags=tags,
                    database=db_schema.name,
                    batch_size=5000
                )

                logger.info(f"Write stats: {stats}")

        elapsed = time.time() - start_time
        logger.info(f"Phase 1 complete in {elapsed:.2f}s")

    def _phase2_backup(self) -> Dict[str, Dict[str, Any]]:
        """Backup all databases"""
        start_time = time.time()

        databases = [schema.name for schema in self.generator.schemas]
        backup_results = self.backup_manager.backup_all_databases(databases)

        # Log summary
        total_points = sum(r['total_points'] for r in backup_results.values())
        total_measurements = sum(len(r['measurements']) for r in backup_results.values())

        elapsed = time.time() - start_time
        logger.info(
            f"Phase 2 complete in {elapsed:.2f}s: "
            f"{total_measurements} measurements, {total_points} points backed up"
        )

        return backup_results

    def _phase3_restore(
        self,
        backup_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Restore all databases"""
        start_time = time.time()

        restore_results = self.backup_manager.restore_all_databases(backup_results)

        # Log summary
        total_points = sum(r['total_points'] for r in restore_results.values())
        total_measurements = sum(len(r['measurements']) for r in restore_results.values())

        elapsed = time.time() - start_time
        logger.info(
            f"Phase 3 complete in {elapsed:.2f}s: "
            f"{total_measurements} measurements, {total_points} points restored"
        )

        return restore_results

    def _phase4_validate(self) -> List:
        """Validate data integrity"""
        start_time = time.time()

        databases = [schema.name for schema in self.generator.schemas]
        comparisons = self.validator.compare_databases(databases, detailed=False)

        elapsed = time.time() - start_time
        logger.info(f"Phase 4 complete in {elapsed:.2f}s")

        return comparisons

    def _phase5_continuous_generation(self):
        """Generate data continuously every N seconds"""
        duration = self.config['test']['test_duration']
        interval = self.config['test']['generation_interval']

        logger.info(
            f"Generating data every {interval}s for {duration}s "
            "(writing to source only)"
        )

        end_time = time.time() + duration
        iteration = 0

        while time.time() < end_time:
            iteration += 1
            logger.info(f"Continuous generation iteration {iteration}")

            for db_schema in self.generator.schemas:
                for measurement in db_schema.measurements:
                    point = self.generator.generate_point(
                        measurement,
                        datetime.utcnow()
                    )
                    self.source_op.write_points(
                        [point],
                        database=db_schema.name
                    )

            time.sleep(interval)

        logger.info(f"Phase 5 complete: {iteration} iterations")


def main():
    """Entry point"""
    try:
        orchestrator = BackupTestOrchestrator()
        success = orchestrator.run_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
