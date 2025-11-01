# Makefile para gestión de dependencias e instalación
# Incluye: install, install-dev, deps-update, deps-show

.PHONY: install install-dev deps-update deps-show

install: ## Instalar dependencias con poetry
	$(call print_blue,📦 Instalando dependencias...)
	$(POETRY) install --with dev,test
	$(call print_green,✅ Dependencias instaladas)

install-dev: ## Instalar en modo desarrollo con pre-commit hooks
	$(call print_blue,🔧 Configurando entorno de desarrollo...)
	$(POETRY) install --with dev,test
	$(POETRY) run pre-commit install
	$(call print_green,✅ Entorno de desarrollo configurado)

deps-update: ## Actualizar dependencias
	$(call print_blue,⬆️  Actualizando dependencias...)
	$(POETRY) update
	$(call print_green,✅ Dependencias actualizadas)

deps-show: ## Mostrar árbol de dependencias
	@echo "Árbol de dependencias de $(PROJECT_NAME):"
	@echo ""
	$(POETRY) show --tree
