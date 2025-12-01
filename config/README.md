# 🔧 Configuration Files

This directory contains all configuration files for development tools.

## 📁 Files

- **`.coveragerc`** - Coverage.py configuration for test coverage
- **`.isort.cfg`** - isort configuration for import sorting
- **`.pylintrc`** - Pylint configuration for code linting
- **`mypy.ini`** - MyPy configuration for type checking
- **`pytest.ini`** - Pytest configuration for testing

## 📝 Notes

These files are referenced by their respective tools and should be kept in this directory for consistency.

### Tool Usage

```bash
# Coverage (from root)
python -m pytest --cov=ctrutils --cov-config=config/.coveragerc

# isort (from root)
isort . --settings-path=config/.isort.cfg

# pylint (from root)
pylint ctrutils --rcfile=config/.pylintrc

# mypy (from root)
mypy ctrutils --config-file=config/mypy.ini

# pytest (from root)
pytest -c config/pytest.ini
```

## 🔄 Makefile Integration

All these tools are integrated in the Makefile. Use `make help` to see available commands.
