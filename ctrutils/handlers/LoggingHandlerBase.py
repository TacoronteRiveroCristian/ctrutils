"""
Este módulo proporciona una clase base, `LoggingHandler`, para la configuración y manejo
de logs en aplicaciones Python. Permite registrar mensajes de log en consola o en un archivo,
y proporciona métodos para personalizar el formato del log y la configuración del logger.
"""

import logging
import os
from typing import Optional


class LoggingHandler:
    """
    Clase `LoggingHandler` que proporciona métodos para manejar y configurar logs de manera reutilizable.

    Esta clase permite la creación y configuración de un logger para registrar mensajes de log en la consola
    o en un archivo. Incluye propiedades para obtener y modificar el formato del log, así como métodos internos
    para gestionar el directorio de logs y los handlers para la salida de los mensajes.

    :param name: Nombre opcional del logger. Si no se especifica, se utiliza el nombre de la clase.
    :type name: str, optional
    :param log_file: Ruta del archivo .log donde se guardarán los logs. Si no se especifica, los logs se muestran en consola.
    :type log_file: str, optional

    **Ejemplo de uso**:

    .. code-block:: python

        from ctrutils.handlers.LoggingHandlerBase import LoggingHandler

        # Crear una instancia de LoggingHandler
        logging_handler = LoggingHandler("MyLogger", "MyLogs.log")

        # Obtener el logger y registrar un mensaje
        logger = logging_handler.get_logger
        logger.info("Logs de prueba")
    """

    def __init__(
        self,
        name: Optional[str] = None,
        log_file: Optional[str] = None,
    ):
        """
        Inicializa el logger al instanciar la clase.

        :param name: Nombre opcional del logger. Si no se especifica, se utiliza el nombre de la clase.
        :type name: str, optional
        :param log_file: Ruta del archivo .log donde se guardarán los logs. Si no se especifica, los logs se muestran en consola.
        :type log_file: str, optional
        """
        self.name = name or self.__class__.__name__
        self.log_file = log_file
        self.current_working_directory = os.getcwd()

        # Configurar el formato de log
        self._log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        # Configurar logger de la instancia
        self._logger = self.configure_logger()

    @property
    def get_logger(self) -> logging.Logger:
        """
        Accede al logger configurado para la instancia.

        :return: El logger actual configurado.
        :rtype: logging.Logger
        """
        return self._logger

    @property
    def get_log_format(self) -> str:
        """
        Accede al formato de log actual.

        :return: El formato de log actual.
        :rtype: str
        """
        return self._log_format

    @get_log_format.setter
    def get_log_format(self, new_format: str) -> None:
        """
        Modifica el formato de log actual.

        :param new_format: El nuevo formato de log.
        :type new_format: str
        :raises ValueError: Si el nuevo formato de log está vacío.
        """
        if not new_format:
            raise ValueError("El formato de log no puede estar vacío.")

        self._log_format = new_format
        for handler in self._logger.handlers:
            handler.setFormatter(logging.Formatter(self._log_format))

    def configure_logger(self) -> logging.Logger:
        """
        Configura y devuelve un logger para la clase base.

        :return: Logger configurado.
        :rtype: logging.Logger
        """
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)

        # Asignar el handler de archivo o de consola según `log_file`
        handler: logging.Handler = (
            self._create_file_handler()
            if self.log_file
            else self._create_stream_handler()
        )
        logger.addHandler(handler)

        return logger

    def _create_log_directory(self) -> None:
        """
        Crea la carpeta para el archivo de log si no existe.
        """
        log_dir = os.path.dirname(self.log_file or "")

        if not log_dir:
            log_dir = self.current_working_directory
            self.log_file = os.path.join(log_dir, self.log_file or "default.log")

        os.makedirs(log_dir, exist_ok=True)

    def _create_file_handler(self) -> logging.FileHandler:
        """
        Crea y configura un `FileHandler` para el archivo de log.

        :return: FileHandler configurado para registrar logs en el archivo especificado.
        :rtype: logging.FileHandler
        """
        self._create_log_directory()
        file_handler = logging.FileHandler(self.log_file or "default.log")
        file_handler.setFormatter(logging.Formatter(self.get_log_format))
        return file_handler

    def _create_stream_handler(self) -> logging.StreamHandler:
        """
        Crea y configura un `StreamHandler` para la salida de logs en consola.

        :return: StreamHandler configurado para mostrar logs en consola.
        :rtype: logging.StreamHandler
        """
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(self.get_log_format))
        return stream_handler
