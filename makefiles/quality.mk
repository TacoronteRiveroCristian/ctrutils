# Makefile para calidad de código
# Incluye: lint, format, check-format, type-check, qa, pre-commit

.PHONY: lint format check-format type-check qa pre-commit

lint: ## Ejecutar linters (pylint y flake8)
	$(call print_blue,🔍 Ejecutando linters...)
	$(POETRY) run pylint $(SRC_DIR) --rcfile=.pylintrc || true
	$(POETRY) run flake8 $(SRC_DIR) --max-line-length=120 --extend-ignore=E203,W503
	$(call print_green,✅ Linting completado)

format: ## Formatear código con black e isort
	$(call print_blue,✨ Formateando código...)
	$(POETRY) run black $(SRC_DIR) $(TEST_DIR)
	$(POETRY) run isort $(SRC_DIR) $(TEST_DIR)
	$(call print_green,✅ Código formateado)

check-format: ## Verificar formato sin modificar archivos
	$(call print_blue,🔍 Verificando formato...)
	$(POETRY) run black --check $(SRC_DIR) $(TEST_DIR)
	$(POETRY) run isort --check-only $(SRC_DIR) $(TEST_DIR)
	$(call print_green,✅ Formato verificado)

type-check: ## Verificar tipos con mypy
	$(call print_blue,🔍 Verificando tipos con mypy...)
	$(POETRY) run mypy $(SRC_DIR) --config-file=mypy.ini
	$(call print_green,✅ Type checking completado)

qa: lint type-check check-format ## Ejecutar todas las verificaciones de calidad
	$(call print_green,✅ Todas las verificaciones de calidad completadas)

pre-commit: ## Ejecutar pre-commit en todos los archivos
	$(call print_blue,🔍 Ejecutando pre-commit hooks...)
	$(POETRY) run pre-commit run --all-files
	$(call print_green,✅ Pre-commit completado)
