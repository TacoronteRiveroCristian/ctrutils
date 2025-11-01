# Guía de Contribución a ctrutils

¡Gracias por tu interés en contribuir a **ctrutils**! 🎉

## 🚀 Inicio Rápido

### 1. Fork y Clone

```bash
# Fork el repositorio en GitHub, luego:
git clone https://github.com/TU_USUARIO/ctrutils.git
cd ctrutils
```

### 2. Setup del Entorno

```bash
# Opción A: Usando Make (recomendado)
make dev

# Opción B: Manual
poetry install --with dev,test
poetry run pre-commit install

# Iniciar InfluxDB para tests de integración
docker run -d -p 8086:8086 \
  -e INFLUXDB_DB=test_db \
  -e INFLUXDB_ADMIN_USER=admin \
  -e INFLUXDB_ADMIN_PASSWORD=admin \
  --name influxdb-test \
  influxdb:1.8
```

### 3. Crear una Rama

```bash
git checkout -b feature/mi-nueva-funcionalidad
# o
git checkout -b fix/mi-bug-fix
```

## 📝 Proceso de Desarrollo

### 1. Escribir Tests Primero (TDD)

```python
# tests/unit/test_mi_feature.py
def test_mi_nueva_funcionalidad():
    # Arrange
    op = InfluxdbOperation(host='localhost', port=8086)
    
    # Act
    resultado = op.mi_nueva_funcionalidad()
    
    # Assert
    assert resultado == esperado
```

### 2. Implementar la Funcionalidad

```python
# ctrutils/database/influxdb/InfluxdbOperation.py
def mi_nueva_funcionalidad(self):
    """
    Descripción clara de lo que hace.
    
    Args:
        parametro1: Descripción
        
    Returns:
        Descripción del retorno
        
    Raises:
        ValueError: Cuando...
    """
    # Implementación
    pass
```

### 3. Ejecutar Tests

```bash
# Tests unitarios (rápido)
make test-unit

# Tests con coverage
make test-coverage

# Todos los tests
make test
```

### 4. Verificar Calidad del Código

```bash
# Formatear código
make format

# Linting
make lint

# Type checking
make type-check

# Todo junto
make qa
```

## ✅ Checklist Antes de Commit

- [ ] Tests escritos y pasando
- [ ] Coverage >80% para código nuevo
- [ ] Código formateado con black
- [ ] Sin errores de pylint/flake8
- [ ] Type hints añadidos
- [ ] Docstrings actualizados
- [ ] CHANGELOG.md actualizado (si aplica)

## 📋 Estándares de Código

### Estilo

- **Formateo**: Black (línea máxima 120 caracteres)
- **Imports**: isort
- **Type hints**: Obligatorios en funciones públicas
- **Docstrings**: Google style

Ejemplo:

```python
from typing import Optional, Dict, Any
import pandas as pd


def process_dataframe(
    df: pd.DataFrame,
    measurement: str,
    tags: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Procesa un DataFrame y lo escribe a InfluxDB.
    
    Args:
        df: DataFrame con datos a procesar
        measurement: Nombre de la medición
        tags: Tags opcionales para los puntos
        
    Returns:
        Diccionario con estadísticas de la operación:
        - successful: Puntos escritos exitosamente
        - failed: Puntos que fallaron
        - duration: Tiempo de ejecución en segundos
        
    Raises:
        ValueError: Si el DataFrame está vacío
        
    Example:
        >>> df = pd.DataFrame({'temp': [25.5, 26.0]})
        >>> stats = process_dataframe(df, 'temperature')
        >>> print(stats['successful'])
        2
    """
    if df.empty:
        raise ValueError("DataFrame no puede estar vacío")
    
    # Implementación
    return {"successful": 0, "failed": 0, "duration": 0.0}
```

### Tests

#### Tests Unitarios

- Mock todas las dependencias externas
- Un test = una funcionalidad
- Nombres descriptivos: `test_<que_hace>_<escenario>_<resultado_esperado>`

```python
def test_validate_value_with_nan_returns_none(self):
    """Test que valores NaN retornan None."""
    result = self.op._validate_value(np.nan)
    self.assertIsNone(result)
```

#### Tests de Integración

- Usan InfluxDB real
- Limpian datos después de ejecutar
- Se pueden saltar si no hay InfluxDB

```python
@unittest.skipIf(SKIP_INTEGRATION, SKIP_MSG)
class TestMyIntegration(unittest.TestCase):
    def setUp(self):
        self.op = InfluxdbOperation(**get_test_config())
        # Setup
    
    def tearDown(self):
        # Cleanup
        pass
```

## 🎯 Tipos de Contribuciones

### 🐛 Bug Fixes

1. Crear issue describiendo el bug
2. Crear rama `fix/descripcion-del-bug`
3. Añadir test que reproduzca el bug
4. Implementar el fix
5. Verificar que el test pasa

### ✨ Nuevas Funcionalidades

1. Crear issue o discusión para validar la idea
2. Crear rama `feature/nombre-funcionalidad`
3. Escribir tests primero (TDD)
4. Implementar funcionalidad
5. Actualizar documentación
6. Actualizar CHANGELOG.md

### 📚 Documentación

- Mejorar docstrings
- Añadir ejemplos
- Actualizar README
- Corregir typos

### 🧪 Tests

- Añadir tests faltantes
- Mejorar coverage
- Tests de casos edge

## 🔄 Pull Request

### Título

Usar conventional commits:

- `feat: añadir funcionalidad X`
- `fix: corregir bug en Y`
- `docs: actualizar documentación de Z`
- `test: añadir tests para W`
- `refactor: mejorar estructura de V`
- `perf: optimizar rendimiento de U`

### Descripción

```markdown
## Descripción
Breve descripción de los cambios

## Tipo de Cambio
- [ ] Bug fix
- [ ] Nueva funcionalidad
- [ ] Breaking change
- [ ] Documentación

## ¿Cómo se ha testeado?
- [ ] Tests unitarios
- [ ] Tests de integración
- [ ] Tests manuales

## Checklist
- [ ] Tests pasan localmente
- [ ] Coverage >80%
- [ ] Código formateado
- [ ] Docstrings actualizados
- [ ] CHANGELOG actualizado
```

## 🏗️ Arquitectura del Proyecto

```
ctrutils/
├── ctrutils/              # Código fuente
│   ├── database/
│   │   └── influxdb/     # Módulo InfluxDB
│   └── scheduler/        # Módulo Scheduler
├── tests/                # Tests
│   ├── unit/            # Tests unitarios
│   ├── integration/     # Tests de integración
│   └── fixtures/        # Datos de prueba
├── docs/                # Documentación (futuro)
└── .github/             # CI/CD workflows
```

## 🎓 Recursos

- [Poetry Documentation](https://python-poetry.org/docs/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Black Code Style](https://black.readthedocs.io/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [InfluxDB Python Client](https://influxdb-python.readthedocs.io/)

## 📞 Obtener Ayuda

- **Issues**: Para bugs y feature requests
- **Discussions**: Para preguntas y ideas
- **Email**: tacoronteriverocristian@gmail.com

## 📜 Código de Conducta

- Ser respetuoso y constructivo
- Aceptar críticas constructivas
- Enfocarse en lo que es mejor para la comunidad
- Mostrar empatía hacia otros miembros

## 🎉 Agradecimientos

¡Gracias por contribuir a ctrutils! Cada contribución, por pequeña que sea, es valiosa. 💪

---

**Nota**: Esta es una guía viva que puede evolucionar. Si tienes sugerencias para mejorarla, ¡abre un PR!
