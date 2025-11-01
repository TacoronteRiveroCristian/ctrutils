# Makefile para limpieza y mantenimiento
# Incluye: clean, clean-cache, clean-build, clean-test, clean-all

.PHONY: clean clean-cache clean-build clean-test clean-pyc clean-all

clean: clean-pyc clean-test clean-build ## Limpiar todos los archivos generados
	$(call print_green,✅ Limpieza completada)

clean-cache: ## Limpiar cache de Python
	$(call print_yellow,🧹 Limpiando cache de Python...)
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*~" -delete 2>/dev/null || true
	$(call print_green,✅ Cache limpiado)

clean-build: ## Limpiar archivos de build
	$(call print_yellow,🧹 Limpiando archivos de build...)
	@rm -rf dist/ 2>/dev/null || true
	@rm -rf build/ 2>/dev/null || true
	@rm -rf *.egg-info 2>/dev/null || true
	@rm -rf .eggs/ 2>/dev/null || true
	$(call print_green,✅ Archivos de build limpiados)

clean-test: ## Limpiar archivos de test
	$(call print_yellow,🧹 Limpiando archivos de test...)
	@rm -rf .pytest_cache/ 2>/dev/null || true
	@rm -rf htmlcov/ 2>/dev/null || true
	@rm -rf .coverage 2>/dev/null || true
	@rm -rf coverage.xml 2>/dev/null || true
	@rm -rf .tox/ 2>/dev/null || true
	$(call print_green,✅ Archivos de test limpiados)

clean-pyc: ## Limpiar archivos .pyc
	$(call print_yellow,🧹 Limpiando archivos .pyc...)
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	$(call print_green,✅ Archivos .pyc limpiados)

clean-all: clean clean-cache ## Limpieza profunda (incluye cache y venv)
	$(call print_yellow,🧹 Limpieza profunda...)
	@rm -rf .venv/ 2>/dev/null || true
	@rm -rf poetry.lock 2>/dev/null || true
	$(call print_green,✅ Limpieza profunda completada)
