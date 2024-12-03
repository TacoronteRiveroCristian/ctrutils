"""
Este módulo proporciona una clase `DateUtils` con métodos útiles para la manipulación
y tratamiento de fechas en aplicaciones Python. Incluye métodos para obtener fechas relativas,
convertir fechas a formato ISO 8601, y obtener el inicio y fin de un día específico.
"""

from datetime import datetime
from typing import Literal, Optional, Union

from dateutil.relativedelta import relativedelta


class DateUtils:
    """
    Clase de utilidades para manipulación de fechas y horas en aplicaciones Python.

    Esta clase proporciona varios métodos para manipular y formatear objetos `datetime`.
    Permite calcular fechas relativas, convertir fechas a formato ISO 8601, y obtener el
    instante de inicio o fin de un día específico.

    **Ejemplo de uso general**:

    .. code-block:: python

        from your_module import DateUtils

        date_utils = DateUtils()

        # Obtener una fecha relativa en formato ISO 8601
        relative_date = date_utils.get_relative_date(days=7, date_format="isoformat")
        print(relative_date)  # Devuelve la fecha dentro de 7 días en formato ISO 8601
    """

    def _return_datetime_format(
        self, datetime: datetime, date_format: str
    ) -> Union[datetime, str]:
        """
        Devuelve una fecha y hora en el formato especificado.

        :param datetime: Fecha y hora a formatear.
        :type datetime: datetime
        :param date_format: Formato de fecha. Puede ser 'isoformat' (ISO 8601) o 'datetime' (objeto datetime).
        :type date_format: str
        :return: La fecha y hora formateada según el parámetro `date_format`.
        :rtype: Union[datetime, str]

        :raises ValueError: Si el `date_format` no es 'isoformat' ni 'datetime'.

        **Ejemplo de uso**:

        .. code-block:: python

            from your_module import DateUtils
            from datetime import datetime

            date_utils = DateUtils()
            formatted_date = date_utils._return_datetime_format(datetime.now(), "isoformat")
            print(formatted_date)  # Devuelve la fecha actual en formato ISO 8601
        """
        if date_format == "isoformat":
            return self.datetime_to_isoformat(datetime)
        elif date_format == "datetime":
            return datetime
        else:
            raise ValueError(
                "Formato de fecha no soportado. Use 'isoformat' o 'datetime'."
            )

    def get_relative_date(
        self,
        months: Optional[int] = 0,
        weeks: Optional[int] = 0,
        days: Optional[int] = 0,
        hours: Optional[int] = 0,
        minutes: Optional[int] = 0,
        seconds: Optional[int] = 0,
        base_datetime: Optional[datetime] = None,
        date_format: Literal["isoformat", "datetime"] = "isoformat",
    ) -> Union[datetime, str]:
        """
        Retorna una fecha relativa en el formato especificado.

        :param months: Cantidad de meses a agregar.
        :type months: int
        :param weeks: Cantidad de semanas a agregar.
        :type weeks: int
        :param days: Cantidad de días a agregar.
        :type days: int
        :param hours: Cantidad de horas a agregar.
        :type hours: int
        :param minutes: Cantidad de minutos a agregar.
        :type minutes: int
        :param seconds: Cantidad de segundos a agregar.
        :type seconds: int
        :param base_datetime: Fecha y hora base. Si no se proporciona, se usa la fecha actual.
        :type base_datetime: datetime
        :param date_format: Formato de fecha. Puede ser 'isoformat' (ISO 8601) o 'datetime' (objeto datetime).
        :type date_format: str
        :return: La fecha relativa en el formato especificado.
        :rtype: Union[datetime, str]

        **Ejemplo de uso**:

        .. code-block:: python

            from your_module import DateUtils

            date_utils = DateUtils()
            future_date = date_utils.get_relative_date(days=1, date_format="isoformat")
            print(future_date)  # Devuelve la fecha de mañana en formato ISO 8601
        """
        if base_datetime is None:
            base_datetime = datetime.now()

        if any(
            period != 0 for period in [months, weeks, days, hours, minutes, seconds]
        ):
            relative_datetime = base_datetime + relativedelta(
                months=months,
                weeks=weeks,
                days=days,
                hours=hours,
                minutes=minutes,
                seconds=seconds,
            )
        else:
            relative_datetime = base_datetime

        return self._return_datetime_format(relative_datetime, date_format)

    def datetime_to_isoformat(self, date: datetime) -> str:
        """
        Convierte una fecha en formato ISO 8601.

        :param date: Fecha a convertir.
        :type date: datetime
        :return: La fecha en formato ISO 8601 como cadena.
        :rtype: str

        **Ejemplo de uso**:

        .. code-block:: python

            from your_module import DateUtils
            from datetime import datetime

            date_utils = DateUtils()
            iso_date = date_utils.datetime_to_isoformat(datetime.now())
            print(iso_date)  # Devuelve la fecha actual en formato ISO 8601
        """
        date = date.replace(microsecond=0)
        return date.isoformat() + "Z"

    def get_start_of_day(
        self,
        date: datetime,
        date_format: Literal["isoformat", "datetime"] = "isoformat",
    ) -> Union[str, datetime]:
        """
        Obtiene el instante inicial del día para una fecha dada.

        :param date: Fecha para la cual se obtiene el instante inicial del día.
        :type date: datetime
        :param date_format: Formato de fecha. Puede ser 'isoformat' o 'datetime'.
        :type date_format: str
        :return: Fecha en el formato especificado correspondiente al inicio del día.
        :rtype: Union[str, datetime]

        **Ejemplo de uso**:

        .. code-block:: python

            from your_module import DateUtils
            from datetime import datetime

            date_utils = DateUtils()
            start_of_day = date_utils.get_start_of_day(datetime.now())
            print(start_of_day)  # Devuelve el inicio del día actual en formato ISO 8601
        """
        _start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        return self._return_datetime_format(_start_of_day, date_format)

    def get_end_of_day(
        self,
        date: datetime,
        date_format: Literal["isoformat", "datetime"] = "isoformat",
    ) -> Union[str, datetime]:
        """
        Obtiene el instante final del día para una fecha dada.

        :param date: Fecha para la cual se obtiene el instante final del día.
        :type date: datetime
        :param date_format: Formato de fecha. Puede ser 'isoformat' o 'datetime'.
        :type date_format: str
        :return: Fecha en el formato especificado correspondiente al final del día.
        :rtype: Union[str, datetime]

        **Ejemplo de uso**:

        .. code-block:: python

            from your_module import DateUtils
            from datetime import datetime

            date_utils = DateUtils()
            end_of_day = date_utils.get_end_of_day(datetime.now())
            print(end_of_day)  # Devuelve el final del día actual en formato ISO 8601
        """
        _end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=0)
        return self._return_datetime_format(_end_of_day, date_format)
