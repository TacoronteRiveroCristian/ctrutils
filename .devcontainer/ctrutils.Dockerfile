# Usar tu imagen base
FROM cristiantr/dev_container_image:latest

ARG WORKDIR="/workspaces/ctrutils"
ARG GITHUB_USERNAME
ARG GITHUB_GMAIL

# Establecer variables de entorno
ENV LANG=es_ES.UTF-8
ENV LANGUAGE=es_ES:es
ENV LC_ALL=es_ES.UTF-8
ENV PYTHONPATH=${PYTHONPATH:-}:${WORKDIR}
ENV WORKDIR=${WORKDIR}

# Cambiar directorio de trabajo
WORKDIR ${WORKDIR}

# Cambiar a usuario root
USER root

# Actualizar el repositorio de paquetes e instalar los que sean necesarios
RUN apt update && apt install -y locales

# Generar el locale español para la documentación de la librería ctrutils
RUN locale-gen es_ES.UTF-8

# Configurar credenciales de GitHub
RUN git config --global user.name "${GITHUB_USERNAME}" && \
    git config --global user.email "${GITHUB_GMAIL}"

# Copiar archivos y configurar permisos
COPY . ${WORKDIR}
RUN chown -R dev_container:dev_container ${WORKDIR} && \
    chmod -R 770 ${WORKDIR} && \
    chmod 600 ${WORKDIR}/.env

# Enlazar python3 con python ya que poetry usa por defecto python y solamente esta python3
RUN ln -s /usr/bin/python3 /usr/bin/python

# Cambiar al usuario sin privilegios
USER dev_container

# Instalar Poetry para la gestión de dependencias en Python
RUN curl -sSL https://install.python-poetry.org | python3 -
# Añadir Poetry al PATH permanentemente para el usuario dev_container
ENV PATH="/home/dev_container/.local/bin:$PATH"

# Instalar las dependencias del proyecto sin instalar el paquete raíz
RUN if [ -f "pyproject.toml" ]; then \
    poetry --version && \
    poetry install --no-root; \
    else echo "pyproject.toml no encontrado"; fi


# Establecer el comando por defecto para ejecutar el contenedor en modo interactivo con bash
CMD ["/bin/bash"]
