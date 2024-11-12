"""
Este módulo proporciona una clase base, LoggingHandler, para la configuración y manejo
de logs en aplicaciones Python. Permite registrar mensajes de log en consola o en un archivo,
y proporciona métodos para personalizar el formato del log y la configuración del logger.
"""

import logging
from logging import FileHandler, StreamHandler
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional


class LoggingHandler:
    """
    Clase para configurar y manejar logs en aplicaciones Python.

    Esta clase permite registrar mensajes de log en consola o en un archivo,
    con opciones para rotar los logs segun un periodo de retencion y mantener
    un numero especifico de copias de respaldo.

    :param log_file: Ruta del archivo .log donde se guardaran los logs. Si no se especifica, los logs se muestran en consola.
    :type log_file: str, opcional
    :param name: Nombre opcional del logger. Si no se especifica, se utiliza el nombre de la clase.
    :type name: str, opcional
    :param log_retention_period: Periodo de retencion de los logs en formato '<n>d' para dias, '<n>w' para semanas, '<n>m' para meses, etc.
    :type log_retention_period: str, opcional
    :param log_backup_period: Numero de copias de respaldo a mantener. Por defecto es 1.
    :type log_backup_period: int, opcional

    **Ejemplo de uso**:

    ```python
    from logging_handler import LoggingHandler

    # Crear una instancia de LoggingHandler para logs en consola
    console_logger = LoggingHandler()
    logger = console_logger.configure_logger()
    logger.info("Mensaje de log en consola")

    # Crear una instancia de LoggingHandler para logs en archivo con rotacion diaria y 7 copias de respaldo
    file_logger = LoggingHandler(
        log_file='app.log',
        log_retention_period='1d',
        log_backup_period=7
    )
    logger = file_logger.configure_logger()
    logger.info("Mensaje de log en archivo")
    ```
    """

    def __init__(
        self,
        log_file: Optional[str] = None,
        name: Optional[str] = None,
        log_retention_period: Optional[str] = None,
        log_backup_period: int = 1,
    ):
        """
        Inicializa una instancia de LoggingHandler con las configuraciones proporcionadas.

        :param log_file: Ruta del archivo .log donde se guardaran los logs. Si no se especifica, los logs se muestran en consola.
        :type log_file: str, opcional
        :param name: Nombre opcional del logger. Si no se especifica, se utiliza el nombre de la clase.
        :type name: str, opcional
        :param log_retention_period: Periodo de retencion de los logs en formato '<n>d' para dias, '<n>w' para semanas, '<n>m' para meses, etc.
        :type log_retention_period: str, opcional
        :param log_backup_period: Numero de copias de respaldo a mantener. Por defecto es 1.
        :type log_backup_period: int, opcional
        """
        self.name: str = name or self.__class__.__name__
        self.log_file: Optional[Path] = Path(log_file) if log_file else None
        self.log_retention_period: Optional[str] = log_retention_period
        self.log_backup_period: int = log_backup_period
        self._log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @property
    def log_format(self) -> str:
        """
        Accede al formato de log actual.

        :return: El formato de log actual.
        :rtype: str
        """
        return self._log_format

    @log_format.setter
    def log_format(self, new_format: str) -> None:
        """
        Modifica el formato de log actual.

        :param new_format: El nuevo formato de log.
        :type new_format: str
        :raises ValueError: Si el nuevo formato de log está vacío.
        """
        if not new_format:
            raise ValueError("El formato de log no puede estar vacío.")

        self._log_format = new_format
        for handler in self.logger.handlers:
            handler.setFormatter(logging.Formatter(self._log_format))

    def _create_log_directory(self) -> None:
        """
        Crea la carpeta para el archivo de log si no existe.
        """
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _create_timed_rotating_file_handler(
        self,
    ) -> TimedRotatingFileHandler:
        """
        Crea y configura un `TimedRotatingFileHandler` para el archivo de log,
        rotando según el periodo de retención (días, semanas o meses).

        :return: TimedRotatingFileHandler configurado para registrar logs en el archivo especificado.
        :rtype: TimedRotatingFileHandler
        :raises ValueError: Si `log_retention_period` o `log_file` son None.
        """
        # Verificar que log_retention_period no sea None
        if self.log_retention_period is None:
            raise ValueError("El periodo de retención de logs no puede ser None.")
        # Verificar que log_file no sea None
        if self.log_file is None:
            raise ValueError("La ruta del archivo de log no puede ser None.")
        # Crear directorio de logs
        self._create_log_directory()
        # Extraer periodo de rotacion en numero de dias o meses y en la letra identificativa D o M
        unit = self.log_retention_period[-1].upper()
        interval = int(self.log_retention_period[:-1])
        # Crear handler del logging
        file_handler = TimedRotatingFileHandler(
            filename=str(self.log_file),
            when=unit,
            interval=interval,
            backupCount=self.log_backup_period,
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter(self.log_format))
        return file_handler

    def _create_file_handler(self) -> FileHandler:
        """
        Crea y configura un `FileHandler` para el archivo de log.

        :return: FileHandler configurado para registrar logs en el archivo especificado.
        :rtype: logging.FileHandler
        """
        # Crear directorio de logs
        self._create_log_directory()
        file_handler = FileHandler(self.log_file or "default.log")
        file_handler.setFormatter(logging.Formatter(self.log_format))
        return file_handler

    def _create_stream_handler(self) -> StreamHandler:
        """
        Crea y configura un `StreamHandler` para la salida de logs en consola.

        :return: StreamHandler configurado para mostrar logs en consola.
        :rtype: logging.StreamHandler
        """
        stream_handler = StreamHandler()
        stream_handler.setFormatter(logging.Formatter(self.log_format))
        return stream_handler

    def configure_logger(self) -> logging.Logger:
        """
        Configura y devuelve un logger para la instancia actual.

        Este metodo establece un logger con el nombre especificado en `self.name` y
        un nivel de registro de INFO. Dependiendo de las propiedades `log_file` y
        `log_retention_period`, asigna el handler adecuado para la salida de los logs:

        - Si `log_file` y `log_retention_period` estan definidos, utiliza un
        `TimedRotatingFileHandler` para rotar los logs segun el periodo especificado.
        - Si solo `log_file` esta definido, utiliza un `FileHandler` para registrar
        los logs en el archivo especificado sin rotacion.
        - Si `log_file` no esta definido, utiliza un `StreamHandler` para mostrar
        los logs en la consola.

        El handler seleccionado se agrega al logger y se devuelve el logger configurado.

        :return: Logger configurado según las propiedades de la instancia.
        :rtype: logging.Logger
        """
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)

        # Declarar el tipo de 'handler' como 'logging.Handler'
        handler: logging.Handler

        # Determinar y asignar el handler adecuado según las propiedades
        if self.log_file and self.log_retention_period:
            handler = self._create_timed_rotating_file_handler()
        elif self.log_file:
            handler = self._create_file_handler()
        else:
            handler = self._create_stream_handler()

        self.logger.addHandler(handler)
        return self.logger
