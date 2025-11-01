# ============================================================================
# Makefile Principal para ctrutils
# ============================================================================
# Este Makefile importa módulos desde makefiles/ para mejor organización
# y escalabilidad a largo plazo.
#
# Estructura:
#   makefiles/
#   ├── variables.mk    - Variables globales y colores
#   ├── install.mk      - Instalación y dependencias
#   ├── test.mk         - Tests (unit, integration, coverage)
#   ├── quality.mk      - Calidad de código (lint, format, type-check)
#   ├── docker.mk       - Gestión de Docker (InfluxDB)
#   ├── build.mk        - Build y publicación
#   ├── clean.mk        - Limpieza de archivos
#   └── workflows.mk    - Workflows complejos (CI, dev, all)
#
# Uso:
#   make help           - Mostrar todos los comandos disponibles
#   make test           - Ejecutar todos los tests
#   make dev            - Setup completo para desarrollo
#   make ci             - Simular CI localmente
# ============================================================================

# Importar variables globales primero
include makefiles/variables.mk

# Importar todos los módulos
include makefiles/install.mk
include makefiles/test.mk
include makefiles/quality.mk
include makefiles/docker.mk
include makefiles/build.mk
include makefiles/clean.mk
include makefiles/workflows.mk

# Declarar todos los PHONYs (evita conflictos con archivos del mismo nombre)
.PHONY: help

# ============================================================================
# Target por defecto: help
# ============================================================================

.DEFAULT_GOAL := help

help: ## 📚 Mostrar esta ayuda con todos los comandos disponibles
	@echo "╔════════════════════════════════════════════════════════════════════╗"
	@echo "║          Comandos disponibles para $(PROJECT_NAME)                          ║"
	@echo "╚════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "$(BLUE)📦 INSTALACIÓN:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' makefiles/install.mk | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)🧪 TESTS:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' makefiles/test.mk | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)✨ CALIDAD DE CÓDIGO:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' makefiles/quality.mk | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)🐳 DOCKER:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' makefiles/docker.mk | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)📦 BUILD Y PUBLICACIÓN:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' makefiles/build.mk | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)🧹 LIMPIEZA:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' makefiles/clean.mk | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)🔄 WORKFLOWS:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' makefiles/workflows.mk | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)💡 Comandos más usados:$(NC)"
	@echo "  $(GREEN)make test$(NC)            - Ejecutar todos los tests"
	@echo "  $(GREEN)make test-unit$(NC)       - Solo tests unitarios (rápido)"
	@echo "  $(GREEN)make test-coverage$(NC)   - Tests con reporte de coverage"
	@echo "  $(GREEN)make dev$(NC)             - Setup completo para desarrollo"
	@echo "  $(GREEN)make ci$(NC)              - Simular CI localmente"
	@echo "  $(GREEN)make format$(NC)          - Formatear código"
	@echo "  $(GREEN)make qa$(NC)              - Verificar calidad completa"
	@echo ""
