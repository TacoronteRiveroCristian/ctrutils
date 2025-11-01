.PHONY: help install test test-unit test-integration test-coverage test-html clean lint format check-format type-check build publish docker-influxdb

# Variables
PYTHON := python3
POETRY := poetry
PYTEST := pytest

help: ## Mostrar esta ayuda
	@echo "Comandos disponibles para ctrutils:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Instalar dependencias con poetry
	$(POETRY) install --with dev,test

install-dev: ## Instalar en modo desarrollo
	$(POETRY) install --with dev,test
	$(POETRY) run pre-commit install

test: ## Ejecutar todos los tests
	$(POETRY) run $(PYTEST) tests/ -v

test-unit: ## Ejecutar solo tests unitarios
	$(POETRY) run $(PYTEST) tests/unit/ -v --tb=short

test-integration: ## Ejecutar solo tests de integración
	$(POETRY) run $(PYTEST) tests/integration/ -v --tb=short

test-coverage: ## Ejecutar tests con coverage
	$(POETRY) run $(PYTEST) tests/ -v --cov=ctrutils --cov-report=term-missing --cov-report=xml

test-html: ## Generar reporte HTML de coverage
	$(POETRY) run $(PYTEST) tests/ -v --cov=ctrutils --cov-report=html --cov-report=term
	@echo "Reporte generado en: htmlcov/index.html"

test-watch: ## Ejecutar tests en modo watch
	$(POETRY) run ptw tests/unit/ -- -v

clean: ## Limpiar archivos generados
	@echo "Limpiando archivos..."
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Limpieza completada"

lint: ## Ejecutar linters (pylint y flake8)
	$(POETRY) run pylint ctrutils --rcfile=.pylintrc || true
	$(POETRY) run flake8 ctrutils --max-line-length=120 --extend-ignore=E203,W503

format: ## Formatear código con black e isort
	$(POETRY) run black ctrutils tests
	$(POETRY) run isort ctrutils tests

check-format: ## Verificar formato sin modificar
	$(POETRY) run black --check ctrutils tests
	$(POETRY) run isort --check-only ctrutils tests

type-check: ## Verificar tipos con mypy
	$(POETRY) run mypy ctrutils --config-file=mypy.ini

qa: lint type-check check-format ## Ejecutar todas las verificaciones de calidad

build: clean ## Construir paquete
	$(POETRY) build

publish: build ## Publicar a PyPI
	$(POETRY) publish

publish-test: build ## Publicar a TestPyPI
	$(POETRY) publish --repository testpypi

docker-influxdb: ## Iniciar InfluxDB en Docker para tests
	@echo "Iniciando InfluxDB 1.8..."
	docker run -d -p 8086:8086 \
		-e INFLUXDB_DB=test_db \
		-e INFLUXDB_ADMIN_USER=admin \
		-e INFLUXDB_ADMIN_PASSWORD=admin \
		--name influxdb-test \
		influxdb:1.8
	@echo "InfluxDB iniciado en localhost:8086"
	@echo "Para detener: docker stop influxdb-test && docker rm influxdb-test"

docker-influxdb-stop: ## Detener y eliminar contenedor de InfluxDB
	docker stop influxdb-test || true
	docker rm influxdb-test || true

version-patch: ## Incrementar version patch (0.0.X)
	$(POETRY) version patch
	@echo "Nueva version: $$($(POETRY) version -s)"

version-minor: ## Incrementar version minor (0.X.0)
	$(POETRY) version minor
	@echo "Nueva version: $$($(POETRY) version -s)"

version-major: ## Incrementar version major (X.0.0)
	$(POETRY) version major
	@echo "Nueva version: $$($(POETRY) version -s)"

deps-update: ## Actualizar dependencias
	$(POETRY) update

deps-show: ## Mostrar árbol de dependencias
	$(POETRY) show --tree

pre-commit: ## Ejecutar pre-commit en todos los archivos
	$(POETRY) run pre-commit run --all-files

ci: lint type-check test-coverage ## Simular CI localmente

dev: install-dev docker-influxdb ## Setup completo para desarrollo
	@echo ""
	@echo "✅ Entorno de desarrollo configurado"
	@echo "   - Dependencias instaladas"
	@echo "   - Pre-commit hooks instalados"
	@echo "   - InfluxDB corriendo en Docker"
	@echo ""
	@echo "Comandos útiles:"
	@echo "  make test-unit       - Ejecutar tests unitarios"
	@echo "  make test-coverage   - Tests con coverage"
	@echo "  make lint            - Verificar código"
	@echo "  make format          - Formatear código"
	@echo ""

all: clean install test lint ## Ejecutar todo (clean, install, test, lint)
