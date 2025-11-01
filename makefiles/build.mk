# Makefile para build y publicación
# Incluye: build, publish, publish-test, version-*

.PHONY: build publish publish-test version-patch version-minor version-major version-show

build: clean ## Construir paquete para distribución
	$(call print_blue,📦 Construyendo paquete...)
	$(POETRY) build
	$(call print_green,✅ Paquete construido en dist/)

publish: build ## Publicar a PyPI
	$(call print_yellow,⚠️  Publicando a PyPI...)
	$(POETRY) publish
	$(call print_green,✅ Paquete publicado en PyPI)

publish-test: build ## Publicar a TestPyPI
	$(call print_blue,📦 Publicando a TestPyPI...)
	$(POETRY) publish --repository testpypi
	$(call print_green,✅ Paquete publicado en TestPyPI)

version-show: ## Mostrar versión actual
	@echo "Versión actual: $(shell $(POETRY) version -s)"

version-patch: ## Incrementar version patch (X.Y.Z -> X.Y.Z+1)
	$(call print_blue,⬆️  Incrementando versión patch...)
	$(POETRY) version patch
	@echo ""
	$(call print_green,✅ Nueva versión: $(shell $(POETRY) version -s))

version-minor: ## Incrementar version minor (X.Y.Z -> X.Y+1.0)
	$(call print_blue,⬆️  Incrementando versión minor...)
	$(POETRY) version minor
	@echo ""
	$(call print_green,✅ Nueva versión: $(shell $(POETRY) version -s))

version-major: ## Incrementar version major (X.Y.Z -> X+1.0.0)
	$(call print_blue,⬆️  Incrementando versión major...)
	$(POETRY) version major
	@echo ""
	$(call print_green,✅ Nueva versión: $(shell $(POETRY) version -s))
