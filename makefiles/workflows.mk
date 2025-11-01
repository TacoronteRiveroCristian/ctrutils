# Makefile para workflows complejos y CI
# Incluye: ci, dev, all, check

.PHONY: ci dev all check status

ci: lint type-check test-coverage ## Simular CI localmente (lint + type-check + tests con coverage)
	$(call print_green,✅ CI local completado exitosamente)

dev: install-dev docker-influxdb ## Setup completo para desarrollo
	@echo ""
	$(call print_green,✅ Entorno de desarrollo configurado)
	@echo ""
	@echo "Configuración completada:"
	@echo "  ✓ Dependencias instaladas"
	@echo "  ✓ Pre-commit hooks configurados"
	@echo "  ✓ InfluxDB corriendo en Docker (localhost:8086)"
	@echo ""
	@echo "Comandos útiles:"
	@echo "  $(BLUE)make test$(NC)            - Ejecutar todos los tests"
	@echo "  $(BLUE)make test-unit$(NC)       - Solo tests unitarios"
	@echo "  $(BLUE)make test-coverage$(NC)   - Tests con coverage"
	@echo "  $(BLUE)make lint$(NC)            - Verificar código"
	@echo "  $(BLUE)make format$(NC)          - Formatear código"
	@echo "  $(BLUE)make qa$(NC)              - Calidad completa"
	@echo ""

all: clean install test lint ## Ejecutar workflow completo (clean + install + test + lint)
	$(call print_green,✅ Workflow completo ejecutado)

check: qa test-coverage docker-check ## Verificación completa antes de commit
	$(call print_green,✅ Todas las verificaciones pasaron - listo para commit)

status: ## Mostrar estado del proyecto
	@echo "Estado del proyecto $(PROJECT_NAME):"
	@echo ""
	@echo "Versión: $(shell $(POETRY) version -s)"
	@echo ""
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Poetry: $(shell $(POETRY) --version)"
	@echo ""
	@echo "Tests disponibles:"
	@echo "  Unit tests:        $(shell find $(TEST_DIR)/unit -name 'test_*.py' | wc -l) archivos"
	@echo "  Integration tests: $(shell find $(TEST_DIR)/integration -name 'test_*.py' | wc -l) archivos"
	@echo ""
	@echo "Estado de servicios:"
	@$(MAKE) docker-check --no-print-directory
