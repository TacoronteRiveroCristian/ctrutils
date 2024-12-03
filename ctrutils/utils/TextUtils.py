"""
Este módulo proporciona una clase `TextUtils` con métodos útiles para la manipulación
y normalización de textos en aplicaciones Python. Incluye métodos para limpiar caracteres
especiales, reemplazar espacios por guiones bajos, y convertir texto a formatos consistentes.
"""

import re

from unidecode import unidecode


class TextUtils:
    """
    Clase de utilidades para la manipulación y normalización de textos en aplicaciones Python.

    Esta clase proporciona varios métodos para limpiar y transformar textos. Permite quitar
    caracteres especiales, reemplazar espacios por guiones bajos, y realizar otras transformaciones.

    **Ejemplo de uso general**:

    .. code-block:: python

        from your_module import TextUtils

        text_utils = TextUtils()

        # Normalizar un texto
        normalized_text = text_utils.normalize_text("Hola, ¿cómo estás? Ñoño")
        print(normalized_text)  # Devuelve 'Hola_como_estas_Nono'
    """

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normaliza un texto eliminando caracteres especiales, reemplazando espacios por '_',
        y transformando caracteres con acentos o especiales a su equivalente ASCII.

        :param text: Texto a normalizar.
        :type text: str
        :return: Texto normalizado.
        :rtype: str

        **Ejemplo de uso**:

        .. code-block:: python

            from your_module import TextUtils

            text_utils = TextUtils()
            normalized_text = text_utils.normalize_text("Hola, ¿cómo estás? Ñoño")
            print(normalized_text)  # Devuelve 'Hola_como_estas_Nono'
        """
        # Convertir caracteres Unicode a ASCII
        ascii_text = unidecode(text)
        # Eliminar caracteres especiales excepto letras, números y espacios
        cleaned_text = re.sub(r"[^a-zA-Z0-9\s]", "", ascii_text)
        # Reemplazar espacios por '_'
        normalized_text = cleaned_text.replace(" ", "_")
        return normalized_text
