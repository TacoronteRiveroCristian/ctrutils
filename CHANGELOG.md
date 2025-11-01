# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [11.0.0] - 2025-11-01

### Added

#### InfluxDB Module - Advanced Features
- **Parallel Write Capabilities**
  - `write_dataframe_parallel()` for concurrent batch processing with ThreadPoolExecutor
  - Configurable max_workers and progress callbacks
  - Thread-safe operations with metrics tracking

- **Downsampling and Continuous Queries**
  - `downsample_data()` for manual aggregation (MEAN, SUM, MAX, MIN, COUNT)
  - `create_continuous_query()` for automatic downsampling
  - `list_continuous_queries()` and `drop_continuous_query()` for CQ management

- **Backup and Restore**
  - `backup_measurement()` to export data as CSV
  - `restore_measurement()` to import from CSV
  - Batch processing for large datasets

- **Data Quality Metrics**
  - `calculate_data_quality_metrics()` for comprehensive analysis
  - Missing data detection and percentage calculation
  - Statistical analysis (mean, std, min, max)
  - Outlier detection using z-score method
  - Unique value counting for categorical fields

- **Advanced Query Builder**
  - `query_builder()` for programmatic query construction
  - `execute_query_builder()` with DataFrame support
  - Support for WHERE conditions, GROUP BY, ORDER BY, LIMIT
  - Operator support (=, >, <, >=, <=, etc.)

- **Monitoring and Reliability**
  - Integrated logging system with `enable_logging()`
  - Metrics tracking (`_metrics` dict) for writes, points, failures, timing
  - Retry logic with exponential backoff
  - Transaction context manager for atomic operations
  - `get_metrics()` and `reset_metrics()` methods

#### Testing Infrastructure
- **Comprehensive Test Suite**
  - Unit tests with mocks (no external dependencies)
  - Integration tests with real InfluxDB
  - Shared fixtures for test data generation
  - 10+ test classes covering all functionality
  - Performance tests for large datasets

- **Test Tools**
  - pytest configuration in pyproject.toml and pytest.ini
  - Coverage configuration (.coveragerc) with >80% target
  - Helper script (run-tests.sh) for easy test execution
  - GitHub Actions CI/CD workflow for automated testing
  - Test markers (unit, integration, slow)
  - Docker setup for InfluxDB test instances

- **Test Dependencies**
  - pytest ^8.3.0
  - pytest-cov ^6.0.0
  - pytest-mock ^3.14.0
  - pytest-asyncio ^0.24.0
  - coverage[toml] ^7.6.0

#### Development Tools
- **Makefile** with common tasks:
  - Test execution (unit, integration, coverage, html)
  - Code quality checks (lint, format, type-check)
  - Build and publish commands
  - Docker InfluxDB management
  - Version bumping helpers
  - Complete dev environment setup

- **Documentation**
  - Comprehensive tests/README.md with usage instructions
  - CONTRIBUTING.md with contribution guidelines
  - .env.example for test configuration
  - Updated main README with testing section

### Changed
- **InfluxDB Module**
  - Removed DateUtils dependency
  - Replaced with internal `_convert_to_utc_iso()` method
  - Now uses only pandas and datetime standard libraries
  - Maintains full backward compatibility

- **Project Structure**
  - Minimalist focus on InfluxDB and Scheduler modules only
  - Removed handler, template, and utils modules
  - Cleaned up documentation dependencies

### Removed
- All Markdown (.md) documentation files from previous structure
- Handler module (diagnostic, logging)
- Template module (backup, email)
- Utils module (date_utils, text_utils)
- Sphinx documentation dependencies
- Unnecessary development dependencies (loki, unidecode, ipykernel)

### Dependencies
- Core: influxdb 5.3.2, pandas 2.2.3, numpy 2.0.0, python-dateutil 2.9.0, apscheduler 3.10.0
- Dev: isort, mypy, pylint, flake8, black, pre-commit
- Test: pytest, pytest-cov, pytest-mock, pytest-asyncio, coverage

### Fixed
- DateUtils import errors after module removal
- All linting errors resolved
- Type hints consistency improved

## [10.x.x] - Previous Versions

See git history for changes in previous versions.

---

## Types of Changes

- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` in case of vulnerabilities
