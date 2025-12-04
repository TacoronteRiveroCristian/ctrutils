# ============================================================================
# Documentation Targets (Sphinx)
# ============================================================================

# Variables
DOCS_SOURCE_DIR = docs_source
DOCS_BUILD_DIR = docs_build
SPHINX_BUILD = $(POETRY) run sphinx-build
SPHINX_AUTOBUILD = $(POETRY) run sphinx-autobuild
SPHINX_OPTS =
SPHINX_OPTS_STRICT = -W --keep-going

# PHONY targets
.PHONY: docs docs-build docs-clean docs-serve docs-check docs-coverage docs-linkcheck docs-install

# ============================================================================
# Documentation Commands
# ============================================================================

docs: docs-build ## 📚 Build documentation (HTML)

docs-build: ## 📚 Build Sphinx documentation
	@echo "$(BLUE)Building documentation...$(NC)"
	@$(SPHINX_BUILD) -b html $(DOCS_SOURCE_DIR) $(DOCS_BUILD_DIR)/html $(SPHINX_OPTS)
	@echo "$(GREEN)Documentation built successfully!$(NC)"
	@echo "$(YELLOW)Open: file://$(PWD)/$(DOCS_BUILD_DIR)/html/index.html$(NC)"

docs-serve: ## 📚 Serve docs with auto-reload (localhost:8000)
	@echo "$(BLUE)Starting documentation server...$(NC)"
	@echo "$(YELLOW)Opening browser at http://localhost:8000$(NC)"
	@$(SPHINX_AUTOBUILD) $(DOCS_SOURCE_DIR) $(DOCS_BUILD_DIR)/html --port 8000 --open-browser $(SPHINX_OPTS)

docs-pdf: ## 📚 Build documentation (PDF)
	@echo "$(BLUE)Building PDF documentation...$(NC)"
	@$(SPHINX_BUILD) -b latex $(DOCS_SOURCE_DIR) $(DOCS_BUILD_DIR)/latex $(SPHINX_OPTS)
	@make -C $(DOCS_BUILD_DIR)/latex all-pdf
	@echo "$(GREEN)PDF built: $(DOCS_BUILD_DIR)/latex/ctrutils.pdf$(NC)"

docs-clean: ## 🧹 Clean documentation build artifacts
	@echo "$(BLUE)Cleaning documentation artifacts...$(NC)"
	@rm -rf $(DOCS_BUILD_DIR)
	@find $(DOCS_SOURCE_DIR) -name '_autosummary' -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Documentation cleaned!$(NC)"

docs-check: ## ✅ Check documentation for errors and warnings
	@echo "$(BLUE)Checking documentation...$(NC)"
	@$(SPHINX_BUILD) -b html $(DOCS_SOURCE_DIR) $(DOCS_BUILD_DIR)/html $(SPHINX_OPTS_STRICT) -q
	@echo "$(GREEN)Documentation check passed!$(NC)"

docs-coverage: ## 📊 Check documentation coverage
	@echo "$(BLUE)Checking documentation coverage...$(NC)"
	@$(SPHINX_BUILD) -b coverage $(DOCS_SOURCE_DIR) $(DOCS_BUILD_DIR)/coverage $(SPHINX_OPTS)
	@cat $(DOCS_BUILD_DIR)/coverage/python.txt
	@echo "$(YELLOW)Full report: $(DOCS_BUILD_DIR)/coverage/python.txt$(NC)"

docs-linkcheck: ## 🔗 Check external links in documentation
	@echo "$(BLUE)Checking external links...$(NC)"
	@$(SPHINX_BUILD) -b linkcheck $(DOCS_SOURCE_DIR) $(DOCS_BUILD_DIR)/linkcheck $(SPHINX_OPTS)
	@echo "$(GREEN)Link check complete!$(NC)"
	@echo "$(YELLOW)Report: $(DOCS_BUILD_DIR)/linkcheck/output.txt$(NC)"

docs-install: ## 📦 Install documentation dependencies
	@echo "$(BLUE)Installing documentation dependencies...$(NC)"
	@poetry install --with docs
	@echo "$(GREEN)Documentation dependencies installed!$(NC)"

docs-autobuild-install: ## 📦 Install sphinx-autobuild for live reload
	@echo "$(BLUE)Installing sphinx-autobuild...$(NC)"
	@poetry add --group docs sphinx-autobuild
	@echo "$(GREEN)sphinx-autobuild installed!$(NC)"
