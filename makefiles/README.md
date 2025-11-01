# 📁 Makefiles Modulares

Esta carpeta contiene los módulos del Makefile organizados por funcionalidad para mejor escalabilidad y mantenibilidad.

## 📋 Estructura

```
makefiles/
├── variables.mk    - Variables globales y funciones helper
├── install.mk      - Instalación y gestión de dependencias
├── test.mk         - Ejecución de tests
├── quality.mk      - Calidad de código (lint, format, type-check)
├── docker.mk       - Gestión de servicios Docker
├── build.mk        - Build y publicación
├── clean.mk        - Limpieza de archivos
└── workflows.mk    - Workflows complejos (CI, dev, all)
```

## 🎯 Filosofía

### Modularidad
Cada archivo `.mk` contiene una categoría lógica de comandos, lo que facilita:
- **Mantenimiento**: Encontrar y editar comandos relacionados
- **Escalabilidad**: Añadir nuevos módulos sin saturar el Makefile principal
- **Reutilización**: Importar módulos en otros proyectos

### Convenciones

#### Nombres de archivos
- `*.mk` - Módulos de Makefile
- Nombres descriptivos de la funcionalidad (`test.mk`, `docker.mk`, etc.)

#### Variables
Todas las variables globales se definen en `variables.mk`:
```makefile
PYTHON := python3
POETRY := poetry
PROJECT_NAME := ctrutils
```

#### Colores
Se usan colores para mejor UX en terminal:
- 🔵 `BLUE` - Acciones en progreso
- 🟢 `GREEN` - Éxito
- 🟡 `YELLOW` - Advertencias
- 🔴 `RED` - Errores

#### Funciones helper
```makefile
$(call print_green,✅ Operación completada)
$(call print_blue,🔍 Procesando...)
```

## 📖 Módulos

### `variables.mk` - Variables Globales
Define todas las variables compartidas y funciones helper de colores.

**Exports:**
- `PYTHON`, `POETRY`, `PYTEST`
- `PROJECT_NAME`, `SRC_DIR`, `TEST_DIR`
- Funciones: `print_green`, `print_blue`, `print_yellow`, `print_red`

### `install.mk` - Instalación
Gestión de dependencias y setup del entorno.

**Comandos:**
- `install` - Instalar dependencias
- `install-dev` - Setup completo de desarrollo
- `deps-update` - Actualizar dependencias
- `deps-show` - Mostrar árbol de dependencias

### `test.mk` - Tests
Ejecución de tests en diferentes modos.

**Comandos:**
- `test` / `test-all` - Todos los tests
- `test-unit` - Solo unitarios
- `test-integration` - Solo integración
- `test-coverage` - Con coverage
- `test-html` - Reporte HTML
- `test-watch` - Modo watch
- `test-failed` - Re-ejecutar fallos
- `test-verbose` - Output detallado
- `test-markers` - Ver markers disponibles

### `quality.mk` - Calidad de Código
Verificaciones de calidad y formateo.

**Comandos:**
- `lint` - Pylint + Flake8
- `format` - Black + isort
- `check-format` - Verificar sin modificar
- `type-check` - Mypy
- `qa` - Todo junto
- `pre-commit` - Hooks de pre-commit

### `docker.mk` - Docker
Gestión de servicios Docker (principalmente InfluxDB).

**Comandos:**
- `docker-influxdb` - Iniciar InfluxDB
- `docker-influxdb-stop` - Detener InfluxDB
- `docker-influxdb-logs` - Ver logs
- `docker-influxdb-restart` - Reiniciar
- `docker-check` - Verificar estado

### `build.mk` - Build y Publicación
Construcción y publicación del paquete.

**Comandos:**
- `build` - Construir paquete
- `publish` - Publicar a PyPI
- `publish-test` - Publicar a TestPyPI
- `version-show` - Ver versión
- `version-patch/minor/major` - Incrementar versión

### `clean.mk` - Limpieza
Limpieza de archivos generados.

**Comandos:**
- `clean` - Limpieza general
- `clean-cache` - Cache de Python
- `clean-build` - Archivos de build
- `clean-test` - Archivos de test
- `clean-pyc` - Archivos .pyc
- `clean-all` - Limpieza profunda

### `workflows.mk` - Workflows Complejos
Combinaciones de comandos para tareas complejas.

**Comandos:**
- `ci` - Simular CI local
- `dev` - Setup completo desarrollo
- `all` - Workflow completo
- `check` - Verificación pre-commit
- `status` - Estado del proyecto

## ➕ Añadir Nuevos Módulos

### 1. Crear archivo `.mk`

```bash
touch makefiles/nueva_funcionalidad.mk
```

### 2. Estructura del módulo

```makefile
# Makefile para nueva funcionalidad
# Descripción de qué hace este módulo

.PHONY: comando1 comando2

comando1: ## Descripción del comando
	$(call print_blue,🔵 Ejecutando comando1...)
	# Implementación
	$(call print_green,✅ Comando1 completado)

comando2: ## Descripción del comando
	$(call print_blue,🔵 Ejecutando comando2...)
	# Implementación
	$(call print_green,✅ Comando2 completado)
```

### 3. Importar en Makefile principal

```makefile
# En el Makefile principal
include makefiles/variables.mk
include makefiles/nueva_funcionalidad.mk
```

### 4. Documentar

Añadir sección en este README explicando el nuevo módulo.

## 🔧 Convenciones de Código

### PHONYs
Siempre declarar targets como PHONY si no generan archivos:
```makefile
.PHONY: test lint format
```

### Comentarios
```makefile
# Comentario de una línea

## Comentario visible en 'make help'

# ============================================================================
# Sección importante
# ============================================================================
```

### Dependencias entre targets
```makefile
build: clean  ## Build depende de clean
	# Implementación
```

### Mensajes de usuario
```makefile
comando: ## Descripción
	$(call print_blue,🔵 Iniciando...)    # Estado
	# Hacer algo
	$(call print_green,✅ Completado)     # Éxito
	@echo ""                               # Separación
	@echo "Información adicional"          # Info
```

## 🎨 Guía de Estilo

### Emojis
Usar emojis consistentes para mejor UX:
- 📦 - Instalación/Paquetes
- 🧪 - Tests
- ✨ - Calidad/Formateo
- 🐳 - Docker
- 🧹 - Limpieza
- 🔍 - Verificación/Búsqueda
- ⚠️ - Advertencia
- ✅ - Éxito
- ❌ - Error
- 🔄 - Proceso/Loop

### Salida
```makefile
# Bueno ✅
$(call print_blue,🧪 Ejecutando tests...)
# Ejecutar tests
$(call print_green,✅ Tests completados)

# Evitar ❌
echo "Running tests"  # Sin color ni emoji
```

## 🚀 Ventajas de esta Estructura

### ✅ Escalabilidad
- Fácil añadir nuevos módulos
- Cada módulo es independiente
- No hay saturación del Makefile principal

### ✅ Mantenibilidad
- Comandos relacionados juntos
- Fácil encontrar y editar
- Código más limpio y organizado

### ✅ Reutilización
- Módulos pueden usarse en otros proyectos
- Variables globales centralizadas
- Funciones helper compartidas

### ✅ Legibilidad
- Estructura clara
- Comentarios descriptivos
- Colores y emojis para mejor UX

### ✅ Testing
- Fácil probar módulos individualmente
- Comandos específicos por categoría
- Separación unit/integration clara

## 📚 Referencias

- [GNU Make Manual](https://www.gnu.org/software/make/manual/)
- [Make Best Practices](https://makefiletutorial.com/)
- [ANSI Color Codes](https://en.wikipedia.org/wiki/ANSI_escape_code#Colors)

## 🤝 Contribuir

Al añadir nuevos comandos:

1. ✅ Elegir el módulo apropiado (o crear uno nuevo)
2. ✅ Añadir comentario `## Descripción` para `make help`
3. ✅ Usar funciones helper de colores
4. ✅ Declarar como `.PHONY` si no genera archivos
5. ✅ Documentar en este README
6. ✅ Probar con `make help` y `make comando`

---

**Última actualización**: Noviembre 2025
**Versión**: 1.0.0
