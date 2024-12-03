"""
Este modulo proporciona una clase base, `ErrorHandler`, que facilita el manejo
y registro de errores de forma reutilizable en aplicaciones Python. Incluye metodos
para capturar y formatear mensajes de error detallados, y puede finalizar el programa
o continuar su ejecucion dependiendo de los parametros.
"""

import logging
import sys
import traceback


class ErrorHandler:
    """
    Clase `ErrorHandler` que proporciona metodos para manejar y registrar errores de manera reutilizable.

    Esta clase esta disenada como una herramienta centralizada para manejar errores en aplicaciones Python.
    Puede registrar mensajes de error detallados en un logger especificado y, opcionalmente, finalizar la ejecucion
    del programa. Los mensajes de error se formatean automaticamente para incluir el rastreo de pila (stack trace)
    si esta disponible.

    Ejemplo de uso:

    .. code-block:: python

        import logging
        from ctrutils.handlers import ErrorHandler

        # Crear un logger
        logger = logging.getLogger(__name__)

        # Instanciar ErrorHandler
        error_handler = ErrorHandler()

        # Manejar un error critico (esto finalizara el programa)
        error_handler.throw_error("Error critico", logger)

        # Manejar un warning
        error_handler.throw_warning("Este es un warning", logger)
    """

    def throw_error(self, message: str, logger: logging.Logger) -> None:
        """
        Maneja los errores registrandolos en el logger especificado y finaliza el programa.

        Este metodo captura el mensaje de error, agrega detalles del rastreo de pila (si estan disponibles)
        y registra el mensaje en el logger especificado. Luego imprime el mensaje en `stderr` y finaliza
        el programa con un codigo de salida.

        :param message: Mensaje de error a registrar.
        :type message: str
        :param logger: Logger que se utilizara para registrar el error. Este logger debe estar configurado
                       previamente para manejar los mensajes de error.
        :type logger: logging.Logger
        :raises SystemExit: Finaliza el programa con un codigo de salida.
        """
        # Obtener el detalle del rastreo de pila si esta disponible
        detailed_traceback = traceback.format_exc()

        # Construir el mensaje de error final
        if not detailed_traceback.strip() or "NoneType: None" in detailed_traceback:
            final_message = message
        else:
            final_message = f"{message}\n{detailed_traceback}"

        # Registrar el mensaje en el logger
        logger.critical(final_message)

        # Imprimir el mensaje en stderr y finalizar el programa
        print(final_message, file=sys.stderr)
        sys.exit(1)
