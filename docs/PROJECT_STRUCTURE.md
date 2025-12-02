# Estructura del Proyecto ctrutils

## Arquitectura del Proyecto

ctrutils es una librería minimalista de utilidades Python enfocada en operaciones con InfluxDB, programación de tareas robusta (tipo Airflow), y logging centralizado.

###  Módulos Principales

```
ctrutils/
├── database/           # Operaciones con InfluxDB
│   └── influxdb/       # Cliente InfluxDB con validación avanzada
├── handler/            # Logging y notificaciones
│   ├── logging/        # Sistema de logging con rotación
│   └── notification/   # Loki y Telegram handlers
└── scheduler/          # Task scheduling production-ready
```

## Reorganización v11.0.0

### Objetivo

Crear una estructura clara y mantenible eliminando archivos innecesarios y agrupando archivos relacionados en carpetas lógicas.

### Estructura Final

```
ctrutils/
├── Archivos raíz (configuración principal)
│   ├── CHANGELOG.md
│   ├── CONTRIBUTING.md
│   ├── LICENSE
│   ├── Makefile
│   ├── README.md
│   ├── poetry.lock
│   ├── pyproject.toml
│   └── requirements.txt
│
├── config/              # Configuraciones de herramientas
│   ├── .coveragerc      # Coverage configuration
│   ├── .isort.cfg       # Import sorting
│   ├── .pylintrc        # Linting rules
│   ├── mypy.ini         # Type checking
│   ├── pytest.ini       # Testing configuration
│   └── README.md
│
├── ctrutils/            # Código fuente
│   ├── database/
│   ├── handler/
│   ├── scheduler/
│   └── __init__.py
│
├── docs/                # Documentación
│   ├── scheduler/       # Docs específicas del scheduler
│   ├── PROJECT_STRUCTURE.md  # Este archivo
│   ├── QUICK_START.md
│   ├── TEST_SUMMARY.md
│   └── README.md
│
├── examples/            # Ejemplos de uso
│   ├── handler_demo.py
│   ├── scheduler_simple.py
│   └── scheduler_advanced_demo.py
│
├── makefiles/           # Makefiles modulares
│   ├── build.mk         # Build y publicación
│   ├── clean.mk         # Limpieza
│   ├── docker.mk        # Docker operations
│   ├── install.mk       # Instalación
│   ├── quality.mk       # Linting y formatting
│   ├── test.mk          # Tests
│   ├── variables.mk     # Variables globales
│   ├── workflows.mk     # Workflows complejos
│   └── README.md
│
└── tests/               # Suite de tests
    ├── fixtures/        # Test fixtures
    ├── integration/     # Tests de integración
    ├── unit/            # Tests unitarios
    ├── __init__.py
    └── README.md
```

### Mejoras Implementadas

Reducción del 40% en items en la raíz (30+ → 18 items)

Documentación centralizada en `docs/`

Configuraciones organizadas en `config/` con symlinks para compatibilidad

Tests claramente separados (unit vs integration)

Sistema modular de Makefiles

Sin archivos generados (logs, coverage, cache)

## Decisiones de Diseño

### 1. Separación de Concerns

**database/**: Aislamiento completo de operaciones de base de datos
- `InfluxdbOperation`: Clase única con toda la funcionalidad InfluxDB
- Validación automática de datos
- Operaciones paralelas para alto volumen

**handler/**: Sistema de logging y notificaciones centralizado
- `logging/`: Handlers estándar con rotación
- `notification/`: Integraciones externas (Loki, Telegram)
- API unificada independiente del backend

**scheduler/**: Task scheduling production-ready
- Inspirado en Airflow pero lightweight
- DAGs con dependencias entre tareas
- Reintentos automáticos con backoff exponencial
- Métricas detalladas por tarea

### 2. Configuración Centralizada

Todos los archivos de configuración en `config/`:
- Fácil de encontrar y modificar
- Symlinks en raíz para compatibilidad con herramientas
- README explicando cada configuración

### 3. Documentación Estructurada

Documentación organizada por propósito:
- **Root README**: Overview y quick start
- **docs/**: Guías detalladas y tutoriales
- **Module READMEs**: API reference específica
- **examples/**: Código funcional y casos de uso

### 4. Testing Robusto

Separación clara de tipos de test:
- **unit/**: Tests rápidos sin dependencias externas
- **integration/**: Tests que requieren servicios (InfluxDB)
- **fixtures/**: Datos y helpers compartidos
- Configuración pytest en `config/pytest.ini`

### 5. Build Modular

Sistema de Makefiles por categoría:
- `build.mk`: Publicación a PyPI
- `test.mk`: Ejecución de tests
- `quality.mk`: Linting, formatting, type-checking
- `clean.mk`: Limpieza de archivos generados
- `workflows.mk`: Comandos complejos (check, release)

Beneficio: Fácil mantener y extender comandos

## Comparativa: Antes y Después

### Antes (Desorganizado)

```
Problema: 30+ archivos en raíz
- 6 archivos MD sueltos (QUICK_START.md, etc.)
- 5 configs sueltas (.pylintrc, mypy.ini, etc.)
- 2 scripts sueltos (.sh files)
- 10+ archivos generados (logs, coverage, cache)
```

### Después (Organizado)

```
Solución: 18 items organizados lógicamente
✓ Documentación → docs/
✓ Configuración → config/ (+ symlinks)
✓ Scripts → Makefiles modulares
✓ Tests → tests/ (unit + integration)
✓ Sin archivos generados (en .gitignore)
```

### Estadísticas

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Items en raíz | 30+ | 18 | -40% |
| Docs sueltos | 6 | 0 | -100% |
| Configs sueltos | 5 | 0 (symlinks) | -100% |
| Scripts sueltos | 2 | 0 | -100% |
| Archivos generados | 10+ | 0 | -100% |
| READMEs | 3 | 7 | +133% |

## Compatibilidad

### Para Herramientas

Las herramientas buscan configs en raíz, por eso mantenemos symlinks:

```bash
# Symlinks en raíz → archivos en config/
.coveragerc → config/.coveragerc
.isort.cfg → config/.isort.cfg
.pylintrc → config/.pylintrc
mypy.ini → config/mypy.ini
pytest.ini → config/pytest.ini
```

Todo sigue funcionando sin cambios:
```bash
pytest           # Encuentra pytest.ini
mypy ctrutils   # Encuentra mypy.ini
pylint ctrutils # Encuentra .pylintrc
```

### Para Desarrolladores

Comandos make siguen igual:
```bash
make test
make lint
make format
make check
```

### Para Usuarios

Sin cambios en la API:
```python
from ctrutils import InfluxdbOperation, Scheduler
from ctrutils.handler import LoggingHandler
```

## Mantenibilidad

### Agregar Nueva Funcionalidad

1. **Código**: Agregar en módulo apropiado (`ctrutils/`)
2. **Tests**: Agregar en `tests/unit/` o `tests/integration/`
3. **Docs**: Agregar en README del módulo
4. **Ejemplos**: Agregar en `examples/`

### Agregar Nuevo Tool/Config

1. **Config**: Agregar en `config/`
2. **Symlink**: Crear symlink en raíz si es necesario
3. **Makefile**: Agregar comando en makefile apropiado
4. **Docs**: Documentar en `config/README.md`

### Publicar Nueva Versión

1. **Cambios**: Documentar en `CHANGELOG.md`
2. **Tests**: Ejecutar `make test`
3. **Quality**: Ejecutar `make check`
4. **Build**: Ejecutar `make build`
5. **Publish**: Ejecutar `make publish`

## Tecnologías y Dependencias

### Runtime Dependencies

- **influxdb**: Cliente InfluxDB
- **pandas**: Manipulación de DataFrames
- **numpy**: Operaciones numéricas
- **apscheduler**: Task scheduling
- **python-dateutil**: Manejo de fechas
- **pytz**: Timezone support

### Development Dependencies

- **pytest**: Testing framework
- **mypy**: Type checking
- **pylint**: Linting
- **black**: Code formatting
- **isort**: Import sorting
- **coverage**: Code coverage

### Build System

- **Poetry**: Dependency management y packaging
- **Make**: Task automation
- **Git**: Version control

## Recursos

- **Repositorio**: [GitHub](https://github.com/TacoronteRiveroCristian/ctrutils)
- **PyPI**: [ctrutils](https://pypi.org/project/ctrutils/)
- **Documentación**: Este directorio (`docs/`)

## Conclusión

La reorganización v11.0.0 transforma ctrutils de un proyecto funcional a uno **production-ready**:

Estructura clara y profesional
Documentación centralizada
Tests organizados
Build system robusto
100% compatible con código existente

El proyecto está listo para crecer sin perder mantenibilidad.

---

**Versión**: 11.0.0
**Fecha**: Noviembre 2025
**Autor**: Cristian Tacoronte Rivero
