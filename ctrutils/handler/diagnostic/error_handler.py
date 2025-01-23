"""
Este modulo proporciona una clase base, `ErrorHandler`, que facilita el manejo
y registro de errores de forma reutilizable en aplicaciones Python. Incluye metodos
para capturar y formatear mensajes de error detallados, y puede finalizar el programa
o continuar su ejecucion dependiendo de los parametros.
"""

import logging
import os
import sys
import traceback
from datetime import datetime


class ErrorHandler:
    """
    Clase para manejar y registrar errores de forma centralizada.

    Esta clase proporciona metodos para capturar, formatear y registrar errores
    de manera detallada, incluyendo informacion del sistema y trazas de la pila.

    Methods:
        throw_error(message: str, logger: logging.Logger) -> None:
            Registra un error critico y finaliza el programa.

    Note:
        Esta clase esta disenada para ser utilizada de forma estatica,
        sin necesidad de instanciarla.
    """

    @classmethod
    def throw_error(cls, message: str, logger: logging.Logger) -> None:
        """
        Maneja los errores registrandolos en el logger especificado y finaliza el programa.

        Este metodo captura automaticamente la informacion de la excepcion actual,
        construye un mensaje de error detallado, lo registra usando el logger
        proporcionado y luego finaliza el programa.

        Args:
            message (str): Mensaje de error personalizado a registrar.
            logger (logging.Logger): Logger que se utilizara para registrar el error.

        Raises:
            SystemExit: Siempre se lanza para finalizar el programa con codigo de salida 1.

        Example:
            >>> try:
            ...     # Codigo que puede lanzar una excepcion
            ...     raise ValueError("Valor invalido")
            ... except ValueError:
            ...     ErrorHandler.throw_error("Se encontro un valor invalido", logger)
            ...
            # Esto registrara el error y finalizara el programa
        """
        exc_info = sys.exc_info()
        error_details = cls._build_error_message(message, exc_info)

        # Registrar el mensaje en el logger
        logger.critical(error_details)

        # Finalizar el programa
        sys.exit(1)

    @staticmethod
    def _build_error_message(message: str, exc_info=None) -> str:
        """
        Construye un mensaje de error detallado.

        Este metodo privado crea un mensaje de error estructurado que incluye
        informacion del sistema, el mensaje de error personalizado y el traceback
        de la excepcion si esta disponible.

        Args:
            message (str): Mensaje de error base personalizado.
            exc_info (tuple, optional): Informacion de la excepcion, normalmente
                                        obtenida de sys.exc_info(). Por defecto es None.

        Returns:
            str: Mensaje de error detallado, incluyendo informacion del sistema
                 y traceback si esta disponible.

        Note:
            Este metodo es para uso interno de la clase ErrorHandler.
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_details = [
            f"Timestamp: {current_time}",
            f"Error Message: {message}",
            f"Script: {os.path.abspath(sys.argv[0])}",
            f"Working Directory: {os.getcwd()}",
            f"Python Version: {sys.version}",
            "Traceback:",
        ]

        if exc_info:
            tb = traceback.extract_tb(exc_info[2])
            for frame in tb:
                error_details.append(
                    f"  File '{frame.filename}', line {frame.lineno}, in {frame.name}"
                )
                error_details.append(f"    {frame.line}")
            error_details.append(f"{exc_info[0].__name__}: {str(exc_info[1])}")
        else:
            error_details.append(traceback.format_exc())

        return "\n".join(error_details)
