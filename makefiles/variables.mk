# Variables globales para todos los Makefiles
# Este archivo define las variables compartidas

PYTHON := python3
POETRY := poetry
PYTEST := pytest
PROJECT_NAME := ctrutils

# Directorios
SRC_DIR := $(PROJECT_NAME)
TEST_DIR := tests
DOCS_DIR := docs

# Colores para output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Funciones de ayuda
define print_green
	@echo "$(GREEN)$1$(NC)"
endef

define print_yellow
	@echo "$(YELLOW)$1$(NC)"
endef

define print_red
	@echo "$(RED)$1$(NC)"
endef

define print_blue
	@echo "$(BLUE)$1$(NC)"
endef
