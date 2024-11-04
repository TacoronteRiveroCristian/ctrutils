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

# Exportar dependencias a requirements.txt
poetry export -f requirements.txt --output requirements.txt --with dev
echo "requirements.txt exportado."

# Menú para seleccionar el tipo de incremento de versión
echo "Seleccione el tipo de incremento de versión:"
echo "1) patch      (e.g., 1.0.0 -> 1.0.1)"
echo "2) minor      (e.g., 1.0.0 -> 1.1.0)"
echo "3) major      (e.g., 1.0.0 -> 2.0.0)"
echo "4) prepatch   (e.g., 1.0.0 -> 1.0.1a0)"
echo "5) preminor   (e.g., 1.0.0 -> 1.1.0a0)"
echo "6) premajor   (e.g., 1.0.0 -> 2.0.0a0)"
echo "7) prerelease (e.g., 1.0.0 -> 1.0.1rc0)"
read -p "Ingrese el número correspondiente o el nombre del incremento: " input

# Determinar el tipo de incremento basado en la entrada del usuario
case $input in
    1 | patch)
        version_type="patch"
        ;;
    2 | minor)
        version_type="minor"
        ;;
    3 | major)
        version_type="major"
        ;;
    4 | prepatch)
        version_type="prepatch"
        ;;
    5 | preminor)
        version_type="preminor"
        ;;
    6 | premajor)
        version_type="premajor"
        ;;
    7 | prerelease)
        version_type="prerelease"
        ;;
    *)
        echo "Entrada no válida. Saliendo del script."
        exit 1
        ;;
esac

# Actualizar la versión del proyecto con Poetry
echo "Actualizando la versión del proyecto a la siguiente $version_type..."
poetry version $version_type

# Actualizar el archivo poetry.lock y reinstalar dependencias
echo "Actualizando el archivo poetry.lock y reinstalando dependencias..."
poetry lock
poetry install

# Construir el paquete con Poetry
echo "Construyendo el paquete con Poetry..."
poetry build

# Preguntar al usuario si desea publicar el paquete
read -p "¿Desea publicar el paquete en PyPI? (s/n): " publish_response
if [[ "$publish_response" =~ ^[sS]$ ]]; then
    # Leer el token de API desde el archivo pypi.key
    if [[ -f "$PROJECT_ROOT/.secrets/pypi.key" ]]; then
        api_token=$(cat "$PROJECT_ROOT/.secrets/pypi.key")
        # Configurar Poetry con el token de API
        poetry config pypi-token.pypi $api_token
        # Publicar el paquete en PyPI
        echo "Publicando el paquete en PyPI..."
        poetry publish --build
    else
        echo "Archivo .key no encontrado en la raíz del proyecto. No se puede publicar el paquete."
    fi
else
    echo "Publicación cancelada por el usuario."
fi

echo "Proceso completado."
