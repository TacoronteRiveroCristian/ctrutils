# Makefile para tests
# Incluye: test, test-unit, test-integration, test-coverage, test-html, test-watch

.PHONY: test test-all test-unit test-integration test-coverage test-html test-watch test-verbose

test: test-all ## Ejecutar todos los tests (unitarios + integración)

test-all: ## Ejecutar todos los tests (unitarios + integración)
	$(call print_blue,🧪 Ejecutando todos los tests...)
	$(POETRY) run $(PYTEST) $(TEST_DIR)/ -v --tb=short
	$(call print_green,✅ Todos los tests completados)

test-unit: ## Ejecutar solo tests unitarios
	$(call print_blue,🧪 Ejecutando tests unitarios...)
	$(POETRY) run $(PYTEST) $(TEST_DIR)/unit/ -v --tb=short
	$(call print_green,✅ Tests unitarios completados)

test-integration: ## Ejecutar solo tests de integración
	$(call print_blue,🧪 Ejecutando tests de integración...)
	$(POETRY) run $(PYTEST) $(TEST_DIR)/integration/ -v --tb=short
	$(call print_green,✅ Tests de integración completados)

test-coverage: ## Ejecutar tests con reporte de coverage
	$(call print_blue,🧪 Ejecutando tests con coverage...)
	$(POETRY) run $(PYTEST) $(TEST_DIR)/ -v --cov=$(PROJECT_NAME) --cov-report=term-missing --cov-report=xml
	$(call print_green,✅ Tests con coverage completados)

test-html: ## Generar reporte HTML de coverage
	$(call print_blue,🧪 Generando reporte HTML de coverage...)
	$(POETRY) run $(PYTEST) $(TEST_DIR)/ -v --cov=$(PROJECT_NAME) --cov-report=html --cov-report=term
	$(call print_green,✅ Reporte generado en: htmlcov/index.html)

test-watch: ## Ejecutar tests en modo watch (requiere pytest-watch)
	$(call print_yellow,👀 Ejecutando tests en modo watch...)
	$(POETRY) run ptw $(TEST_DIR)/unit/ -- -v

test-verbose: ## Ejecutar tests con output verbose completo
	$(call print_blue,🧪 Ejecutando tests con output verbose...)
	$(POETRY) run $(PYTEST) $(TEST_DIR)/ -vv --tb=long

test-failed: ## Ejecutar solo los tests que fallaron en la última ejecución
	$(call print_blue,🧪 Re-ejecutando tests que fallaron...)
	$(POETRY) run $(PYTEST) $(TEST_DIR)/ -v --lf

test-markers: ## Mostrar todos los markers disponibles
	@echo "Markers disponibles:"
	@echo ""
	$(POETRY) run $(PYTEST) --markers
