# Usar tu imagen base
FROM cristiantr/dev_container_image:latest

# Actualizar el repositorio de paquetes e instalar los que sean necesarios
RUN sudo apt update && sudo apt install -y locales

# Generar el locale español para la documentación de la librería ctrutils
RUN sudo locale-gen es_ES.UTF-8

# Establecer el locale español como predeterminado
ENV LANG=es_ES.UTF-8
ENV LANGUAGE=es_ES:es
ENV LC_ALL=es_ES.UTF-8

# Instalar Poetry para la gestión de dependencias en Python
RUN curl -sSL https://install.python-poetry.org | python3.10 -

# Añadir Poetry al PATH permanentemente para el usuario dev_container
ENV PATH="/home/dev_container/.local/bin:$PATH"

# Configurar Poetry para no crear entornos virtuales al usar Docker (o puedes cambiar a true si prefieres virtualenvs)
RUN poetry config virtualenvs.create true
RUN poetry config virtualenvs.in-project true

# Establecer el directorio de trabajo
WORKDIR /workspaces/ctutils

# Copiar todo lo que hay actualmente en la carpeta del proyecto
COPY . .

# Instalar las dependencias del proyecto sin instalar el paquete raíz
RUN if [ -f "pyproject.toml" ]; then poetry install --no-root; fi

# Configurar Poetry para no mostrar warnings
RUN poetry config warnings.export false

# Establecer el comando por defecto para ejecutar el contenedor en modo interactivo con bash
CMD ["/bin/bash"]
