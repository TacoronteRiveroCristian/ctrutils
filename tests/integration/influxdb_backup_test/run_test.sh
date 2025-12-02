#!/bin/bash
set -e

echo "========================================"
echo "InfluxDB Backup Integration Test"
echo "========================================"

# Cleanup previous runs
echo "Cleaning up previous test runs..."
docker-compose down -v 2>/dev/null || true
rm -rf backup_data/* logs/* 2>/dev/null || true

# Create directories
mkdir -p backup_data logs

# Start containers
echo "Starting containers..."
docker-compose up --build -d

# Wait for test to complete
echo "Running test (follow logs with Ctrl+C to detach)..."
docker-compose logs -f python-generator

# Wait for generator to exit
docker wait influxdb-backup-test-generator

# Check exit code
EXIT_CODE=$(docker inspect influxdb-backup-test-generator --format='{{.State.ExitCode}}')

echo ""
echo "========================================"
if [ "$EXIT_CODE" -eq 0 ]; then
    echo "TEST PASSED"
    echo "========================================"
else
    echo "TEST FAILED (exit code: $EXIT_CODE)"
    echo "========================================"
fi

# Show report if available
if [ -f logs/test_report.json ]; then
    echo ""
    echo "Test report saved to: logs/test_report.json"
fi

# Cleanup
echo ""
echo "Cleaning up containers..."
docker-compose down -v

exit $EXIT_CODE
