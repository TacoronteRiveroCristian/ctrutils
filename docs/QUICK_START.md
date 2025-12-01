# 🚀 Quick Start - ctrutils

Guía rápida para empezar a trabajar con **ctrutils**.

## ⚡ Setup en 30 segundos

```bash
# 1. Clonar repositorio
git clone https://github.com/TacoronteRiveroCristian/ctrutils.git
cd ctrutils

# 2. Setup completo (deps + pre-commit + InfluxDB en Docker)
make dev

# 3. Verificar que todo funciona
make test-unit
```

✅ ¡Listo! Entorno configurado y tests pasando.

---

## 📋 Comandos Más Usados

### Durante Desarrollo

```bash
# Ejecutar tests rápidos (unitarios, 2-5 seg)
make test-unit

# Formatear código antes de commit
make format

# Ver estado del proyecto
make status
```

### Antes de Commit

```bash
# Opción 1: Verificación completa (recomendado)
make check
# Ejecuta: qa + test-coverage + docker-check

# Opción 2: Por separado
make format          # Formatear
make qa              # Lint + type-check + format-check
make test-coverage   # Tests con coverage
```

### Tests

```bash
make test              # Todos (unit + integration)
make test-unit         # Solo unitarios (rápido)
make test-integration  # Solo integración (requiere InfluxDB)
make test-coverage     # Con reporte de coverage
make test-html         # Generar reporte HTML
```

### Docker

```bash
make docker-influxdb   # Iniciar InfluxDB
make docker-check      # Verificar estado
make docker-influxdb-stop  # Detener
```

### Ver Todos los Comandos

```bash
make help
```

---

## 🎯 Workflows Comunes

### Añadir Nueva Funcionalidad

```bash
# 1. Crear rama
git checkout -b feature/nueva-funcionalidad

# 2. Escribir tests primero (TDD)
# Editar: tests/unit/test_*.py

# 3. Implementar funcionalidad
# Editar: ctrutils/...

# 4. Ejecutar tests
make test-unit

# 5. Formatear y verificar
make format
make qa

# 6. Tests completos
make test-coverage

# 7. Commit
git add .
git commit -m "feat: descripción de la funcionalidad"
```

### Fix de Bug

```bash
# 1. Reproducir con test
# Añadir test que falla en tests/unit/

# 2. Ejecutar test que falla
make test-unit

# 3. Implementar fix
# Editar código

# 4. Verificar fix
make test-unit

# 5. Tests completos
make check

# 6. Commit
git commit -m "fix: descripción del bug"
```

### Preparar Release

```bash
# 1. Verificar todo
make ci

# 2. Actualizar versión
make version-patch  # o version-minor / version-major

# 3. Actualizar CHANGELOG.md
# Editar manualmente

# 4. Build
make build

# 5. Publicar (si es release oficial)
make publish  # o publish-test para TestPyPI
```

---

## 📖 Documentación Completa

- **README.md** - Descripción general del proyecto
- **tests/README.md** - Guía completa de tests
- **makefiles/README.md** - Documentación de Makefiles
- **CONTRIBUTING.md** - Guía de contribución
- **CHANGELOG.md** - Historial de cambios
- **TEST_SUMMARY.md** - Resumen de tests implementados
- **MAKEFILE_SUMMARY.md** - Resumen de Makefile modular

---

## 🆘 Troubleshooting

### "Command not found: make"

```bash
# macOS
brew install make

# Linux
sudo apt install make  # Debian/Ubuntu
sudo yum install make  # RHEL/CentOS
```

### "Poetry not found"

```bash
# Instalar Poetry
curl -sSL https://install.python-poetry.org | python3 -

# O con pip
pip install poetry
```

### "InfluxDB connection refused"

```bash
# Iniciar InfluxDB en Docker
make docker-influxdb

# Verificar estado
make docker-check

# Ver logs
make docker-influxdb-logs
```

### "Tests failing"

```bash
# Limpiar cache y re-ejecutar
make clean
make test-unit

# Ver output verbose
make test-verbose

# Solo ejecutar tests que fallaron
make test-failed
```

---

## 💡 Tips

### Acelerar Desarrollo

1. **Usa `make test-unit`** durante desarrollo (rápido)
2. **`make test-integration`** solo cuando sea necesario
3. **`make test-watch`** para auto-ejecutar tests al guardar
4. **`make format`** antes de cada commit
5. **`make check`** antes de push

### Mantener Código Limpio

```bash
# Formatear automáticamente
make format

# Verificar calidad
make qa

# Pre-commit hooks (configurado automáticamente con make dev)
git commit -m "..."  # Hooks se ejecutan automáticamente
```

### Trabajar con Tests

```bash
# Solo un archivo de tests
pytest tests/unit/test_influxdb_operation.py -v

# Solo una clase
pytest tests/unit/test_influxdb_operation.py::TestInfluxdbOperationInit -v

# Solo un test específico
pytest tests/unit/test_influxdb_operation.py::TestInfluxdbOperationInit::test_init_with_all_params -v
```

---

## 🎓 Aprender Más

### Estructura del Proyecto

```
ctrutils/
├── ctrutils/          # Código fuente
│   ├── database/      # Módulo InfluxDB
│   └── scheduler/     # Módulo Scheduler
├── tests/             # Tests
│   ├── unit/         # Tests unitarios
│   ├── integration/  # Tests de integración
│   └── fixtures/     # Datos de prueba
├── makefiles/         # Makefiles modulares
└── ...
```

### Módulos Principales

**InfluxdbOperation** - Cliente avanzado de InfluxDB
```python
from ctrutils import InfluxdbOperation

influx = InfluxdbOperation(host='localhost', port=8086)
influx.write_dataframe(df, measurement='datos')
```

**Scheduler** - Programador de tareas
```python
from ctrutils import Scheduler

scheduler = Scheduler()
scheduler.add_job(func, 'interval', hours=1)
scheduler.start()
```

---

## 🤝 Contribuir

¿Quieres contribuir? ¡Genial!

1. Lee [CONTRIBUTING.md](CONTRIBUTING.md)
2. Setup: `make dev`
3. Crea rama: `git checkout -b feature/tu-feature`
4. Implementa con TDD
5. Verifica: `make check`
6. Crea Pull Request

---

## 📞 Ayuda

- **Issues**: https://github.com/TacoronteRiveroCristian/ctrutils/issues
- **Email**: tacoronteriverocristian@gmail.com

---

¡Happy coding! 🎉
