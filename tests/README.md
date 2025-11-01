# Tests para ctrutils

Esta carpeta contiene todos los tests del proyecto `ctrutils`.

## Estructura

```
tests/
├── __init__.py              # Package init
├── fixtures/                # Datos de prueba y configuraciones
│   └── __init__.py
├── unit/                    # Tests unitarios (sin dependencias externas)
│   ├── test_influxdb_operation.py
│   └── test_scheduler.py
└── integration/             # Tests de integración (con InfluxDB real)
    └── test_influxdb_integration.py
```

## Tipos de Tests

### Tests Unitarios (`unit/`)
- **No requieren** dependencias externas (InfluxDB, etc.)
- Usan mocks para simular dependencias
- Rápidos de ejecutar
- Verifican lógica de negocio aislada

### Tests de Integración (`integration/`)
- **Requieren** InfluxDB corriendo
- Prueban interacción con sistemas reales
- Más lentos pero más completos
- Verifican comportamiento end-to-end

## Ejecutar Tests

### Instalar dependencias de test

```bash
# Con poetry (recomendado)
poetry install --with dev

# O con pip
pip install pytest pytest-cov pytest-mock
```

### Ejecutar todos los tests

```bash
pytest
```

### Ejecutar solo tests unitarios (rápido)

```bash
pytest tests/unit/ -v
```

### Ejecutar solo tests de integración

```bash
pytest tests/integration/ -v
```

### Ejecutar con coverage

```bash
# Con reporte en terminal
pytest --cov=ctrutils --cov-report=term-missing

# Generar reporte HTML
pytest --cov=ctrutils --cov-report=html
# Ver en: htmlcov/index.html
```

### Ejecutar tests específicos

```bash
# Un archivo específico
pytest tests/unit/test_influxdb_operation.py -v

# Una clase específica
pytest tests/unit/test_influxdb_operation.py::TestInfluxdbOperationInit -v

# Un test específico
pytest tests/unit/test_influxdb_operation.py::TestInfluxdbOperationInit::test_init_with_all_params -v
```

## Configuración para Tests de Integración

Los tests de integración requieren una instancia de InfluxDB. Configurar mediante variables de entorno:

```bash
export INFLUXDB_TEST_HOST=localhost
export INFLUXDB_TEST_PORT=8086
export INFLUXDB_TEST_USER=admin
export INFLUXDB_TEST_PASSWORD=admin
export INFLUXDB_TEST_DATABASE=test_db
```

### Usar Docker para InfluxDB

```bash
# InfluxDB 1.8 (compatible con este proyecto)
docker run -d -p 8086:8086 \
  -e INFLUXDB_DB=test_db \
  -e INFLUXDB_ADMIN_USER=admin \
  -e INFLUXDB_ADMIN_PASSWORD=admin \
  --name influxdb-test \
  influxdb:1.8
```

## Markers

Los tests tienen markers para facilitar la selección:

```bash
# Solo tests unitarios
pytest -m unit

# Solo tests de integración
pytest -m integration

# Excluir tests lentos
pytest -m "not slow"
```

## Coverage

El proyecto mantiene un objetivo de **>80% coverage** para código crítico.

```bash
# Ver coverage actual
pytest --cov=ctrutils --cov-report=term-missing

# Generar reporte HTML detallado
pytest --cov=ctrutils --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## CI/CD

Los tests se ejecutan automáticamente en CI/CD:

- **Tests unitarios**: En cada commit/PR
- **Tests de integración**: En cada PR antes de merge
- **Coverage**: Se genera reporte y se sube a codecov

## Escribir Nuevos Tests

### Ejemplo: Test Unitario

```python
import unittest
from unittest.mock import Mock, patch
from ctrutils.database.influxdb import InfluxdbOperation

class TestNewFeature(unittest.TestCase):
    @patch('ctrutils.database.influxdb.InfluxdbOperation.InfluxDBClient')
    def test_my_feature(self, mock_client):
        # Arrange
        op = InfluxdbOperation(host='localhost', port=8086)

        # Act
        result = op.some_method()

        # Assert
        self.assertEqual(result, expected_value)
```

### Ejemplo: Test de Integración

```python
import unittest
from ctrutils.database.influxdb import InfluxdbOperation
from tests.fixtures import get_test_config

class TestNewIntegration(unittest.TestCase):
    def setUp(self):
        config = get_test_config()
        self.op = InfluxdbOperation(**config)

    def test_real_operation(self):
        # Test con InfluxDB real
        result = self.op.some_operation()
        self.assertTrue(result)
```

## Fixtures

La carpeta `fixtures/` contiene utilidades para crear datos de prueba:

```python
from tests.fixtures import (
    create_sample_dataframe,
    create_time_series_with_gaps,
    create_large_dataframe,
    get_test_config,
)

# Usar en tests
df = create_sample_dataframe(rows=100, with_nans=True)
config = get_test_config()
```

## Troubleshooting

### "No module named 'ctrutils'"

Instalar el paquete en modo desarrollo:

```bash
pip install -e .
# o
poetry install
```

### "InfluxDB connection refused"

Verificar que InfluxDB esté corriendo:

```bash
# Verificar status
docker ps | grep influxdb

# Ver logs
docker logs influxdb-test
```

### Tests lentos

Usar solo tests unitarios durante desarrollo:

```bash
pytest tests/unit/ -v
```

## Contribuir

Al agregar nueva funcionalidad:

1. ✅ Escribir tests unitarios primero (TDD)
2. ✅ Añadir tests de integración si aplica
3. ✅ Verificar coverage `>80%` para código nuevo
4. ✅ Todos los tests deben pasar antes de PR

```bash
# Verificar antes de commit
pytest --cov=ctrutils --cov-report=term-missing
```
