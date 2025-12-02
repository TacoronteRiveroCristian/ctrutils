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

test-coverage-warn: ## Tests con warnings de coverage (no falla build)
	$(call print_blue,🧪 Ejecutando tests con coverage warnings...)
	@$(POETRY) run $(PYTEST) $(TEST_DIR)/ -v --cov=$(PROJECT_NAME) --cov-report=term-missing --cov-report=xml --cov-branch || true
	@echo ""
	@if [ -f coverage.xml ]; then \
		echo "$(shell tput setaf 3)⚠️  Verificando cobertura de módulos...$(shell tput sgr0)"; \
		INFLUXDB_COV=$$(python3 -c "import xml.etree.ElementTree as ET; tree = ET.parse('coverage.xml'); root = tree.getroot(); pkg = root.find('.//package[@name=\"ctrutils/database/influxdb\"]'); print(round(float(pkg.attrib['line-rate']) * 100, 2)) if pkg is not None else print('0')" 2>/dev/null || echo "0"); \
		SCHEDULER_COV=$$(python3 -c "import xml.etree.ElementTree as ET; tree = ET.parse('coverage.xml'); root = tree.getroot(); pkg = root.find('.//package[@name=\"ctrutils/scheduler\"]'); print(round(float(pkg.attrib['line-rate']) * 100, 2)) if pkg is not None else print('0')" 2>/dev/null || echo "0"); \
		echo ""; \
		echo "📊 Cobertura por módulo:"; \
		echo "  - InfluxDB: $$INFLUXDB_COV% (objetivo: 80%+)"; \
		echo "  - Scheduler: $$SCHEDULER_COV% (objetivo: 80%+)"; \
		echo ""; \
		if [ "$$(echo "$$INFLUXDB_COV < 80" | bc 2>/dev/null || echo 1)" -eq 1 ]; then \
			echo "$(shell tput setaf 3)⚠️  WARNING: InfluxDB coverage está bajo 80%$(shell tput sgr0)"; \
		fi; \
		if [ "$$(echo "$$SCHEDULER_COV < 80" | bc 2>/dev/null || echo 1)" -eq 1 ]; then \
			echo "$(shell tput setaf 3)⚠️  WARNING: Scheduler coverage está bajo 80%$(shell tput sgr0)"; \
		fi; \
	fi
	$(call print_green,✅ Tests completados - ver warnings arriba)

test-edge-cases: ## Solo tests de edge cases
	$(call print_blue,🧪 Ejecutando tests de edge cases...)
	$(POETRY) run $(PYTEST) $(TEST_DIR)/ -v -m edge_case
	$(call print_green,✅ Tests de edge cases completados)

test-docker: docker-test-up test-integration docker-test-down ## Ciclo completo Docker
	$(call print_green,✅ Ciclo completo de tests con Docker completado)
