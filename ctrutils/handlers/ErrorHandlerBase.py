"""
Este módulo proporciona una clase base, `ErrorHandler`, que facilita el manejo
y registro de errores de forma reutilizable en aplicaciones Python. Incluye métodos
para capturar y formatear mensajes de error detallados, y puede finalizar el programa
o continuar su ejecución dependiendo de los parámetros.
"""

import logging
import re
import sys
import traceback


class ErrorHandler:
    """
    Clase `ErrorHandler` que proporciona métodos para manejar y registrar errores de manera reutilizable.

    Esta clase está diseñada para ser una herramienta centralizada de manejo de errores en aplicaciones Python.
    Puede registrar mensajes de error detallados en un logger especificado y, opcionalmente, finalizar la ejecución
    del programa. Los mensajes de error se formatean automáticamente para incluir el rastreo de pila (stack trace)
    cuando está disponible.

    **Ejemplo de uso**:

    .. code-block:: python

        import logging
        from ctrutils.handlers import ErrorHandler

        # Crear un logger
        logger = logging.getLogger(__name__)

        # Instanciar ErrorHandler
        error_handler = ErrorHandler()

        # Manejar un error crítico (esto finalizará el programa)
        error_handler.handle_error("Error crítico", logger, exit_code=1)

        # Manejar un error no crítico (esto permite que el programa continúe)
        error_handler.handle_error("Error no crítico", logger, exit_code=0)
    """

    def handle_error(
        self, message: str, logger: logging.Logger, exit_code: int = 1
    ) -> None:
        """
        Maneja los errores registrándolos en el logger especificado y, opcionalmente, finaliza el programa.

        Este método captura el mensaje de error, agrega detalles del rastreo de pila (si están disponibles),
        y registra el mensaje en el logger especificado. Si el `exit_code` es igual a 1, el método
        imprime el mensaje de error en `stderr` y termina el programa con el código de salida proporcionado.
        Si `exit_code` es diferente de 1, simplemente registra el error y permite que el programa continúe.

        :param message: Mensaje de error a registrar en el logger y, opcionalmente, en `stderr`.
        :type message: str
        :param logger: Logger que se utilizará para registrar el error. Este logger debe estar configurado
                       previamente para manejar los mensajes de error.
        :type logger: logging.Logger
        :param exit_code: Código de salida del programa (por defecto es 1). Si `exit_code` es igual a 1, el método
                          finaliza la ejecución del programa. Si es diferente de 1, el programa continúa ejecutándose.
        :type exit_code: int, optional

        :raises SystemExit: Si `exit_code` es igual a 1, se termina el programa con el código de salida proporcionado.

        **Nota**:
            Si no se ha producido ninguna excepción antes de llamar a este método,
            `traceback.format_exc()` no agregará detalles de rastreo adicionales al mensaje.
        """

        # Obtener detalle del error
        detailed_traceback = traceback.format_exc()

        # Construir mensaje de error final
        if re.search("NoneType: None", detailed_traceback):
            message = f"{message}"
        else:
            message = f"{message}\n{detailed_traceback}"

        # Mostrar el error crítico en consola y finalizar el programa
        if exit_code == 1:
            print(message, file=sys.stderr)
            logger.critical(message + "\n")
            sys.exit(exit_code)
        else:
            logger.error(message)
