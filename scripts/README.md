# 🚀 Scripts

This directory contains utility scripts for project management.

## 📁 Scripts

### `publish-project.sh`
Publishes the project to PyPI.

**Usage:**
```bash
./scripts/publish-project.sh
```

**What it does:**
- Builds the package
- Publishes to PyPI using poetry

### `run-tests.sh`
Runs the complete test suite with coverage.

**Usage:**
```bash
./scripts/run-tests.sh
```

**What it does:**
- Runs all unit and integration tests
- Generates coverage report
- Shows test summary

## 📝 Notes

Make sure scripts are executable:
```bash
chmod +x scripts/*.sh
```

## 🔄 Alternative: Use Makefile

These scripts are also integrated in the Makefile:
```bash
make test        # Run tests
make publish     # Publish to PyPI
```

See `make help` for all available commands.
