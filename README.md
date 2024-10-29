
# ctrutils

**ctrutils** es una librería de utilidades en Python creada para simplificar y automatizar tareas comunes en ciencia de datos y desarrollo. Este proyecto está en desarrollo y puede estar sujeto a cambios.

## Requisitos

Para trabajar en este proyecto solo se necesita instalar la herramienta docker y VScode ya que el entorno de desarrollo se encuentra en un contenedor docker a partir de la imagen personalizada `cristiantr/dev_container_image`.

## Clonar el proyecto

Clona este repositorio para obtener una copia local:

```bash
git clone https://github.com/CristianTacoronteRivero/ctutils.git
cd ctutils
```

## Instalación de Dependencias

Una vez que estés en el directorio del proyecto, instala las dependencias usando `Poetry`:

```bash
poetry install
```

Este comando instalará todas las dependencias del proyecto, incluidas las de desarrollo, definidas en `pyproject.toml`.

## Generación de Documentación y requerimientos

Para generar la documentación del proyecto, utiliza el script `generate_docs.sh`, que automatiza el proceso de creación de archivos `.rst` y compila la documentación en HTML.

Ejecuta el script con:

```bash
./generate_docs.sh
```

### Desglose del Script

El script `generate_docs.sh` realiza los siguientes pasos:

1. **Generación de archivos `.rst`**: Genera archivos `.rst` para todos los módulos de `ctrutils`.
2. **Compilación de la documentación en HTML**: Utiliza `sphinx-build` para generar la documentación en formato HTML en el directorio `docs/build/html`.
3. **Exportación de requirements.txt**: Exporta el archivo `requirements.txt` con las dependencias, incluidas las de desarrollo.

Después de ejecutar el script, encontrarás la documentación generada en `docs/build/html`, lista para ser visualizada en un navegador.

## Contribuciones

¡Las contribuciones son bienvenidas! Si encuentras algún problema o tienes alguna mejora, no dudes en abrir un issue o enviar un pull request.
