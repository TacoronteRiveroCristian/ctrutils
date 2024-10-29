#!/bin/bash

# Directorios de origen y compilación
PROJECT_ROOT=$(pwd)
DOCS_SOURCE_DIR="$PROJECT_ROOT/docs/source"
DOCS_BUILD_DIR="$PROJECT_ROOT/docs/build/html"

# Paso 1: Genera los archivos .rst para todos los módulos de ctrutils (sobrescribe los existentes)
echo "Generando archivos .rst para los módulos..."
sphinx-apidoc -o "$DOCS_SOURCE_DIR" "$PROJECT_ROOT/ctrutils" --force

# Paso 2: Compila la documentación en HTML
echo "Compilando documentación en HTML..."
sphinx-build -b html "$DOCS_SOURCE_DIR" "$DOCS_BUILD_DIR"

echo "Documentación generada con éxito en $DOCS_BUILD_DIR."

poetry export -f requirements.txt --output requirements.txt
echo "requirements.txt exportado."
