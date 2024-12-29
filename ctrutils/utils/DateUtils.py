"""
Este módulo proporciona una clase `DateUtils` con métodos útiles para la manipulación
y tratamiento de fechas en aplicaciones Python. Incluye métodos para obtener fechas relativas,
convertir fechas a diferentes formatos, y obtener el inicio y fin de un día específico.
"""

from datetime import datetime
from typing import Literal, Optional, Union

import pytz  # type: ignore
from dateutil.parser import parse  # type: ignore
from dateutil.relativedelta import relativedelta  # type: ignore


class DateUtils:
    """
    Clase de utilidades para manipulación de fechas y horas en aplicaciones Python.

    Proporciona varios métodos para manipular y formatear objetos `datetime`. Permite calcular
    fechas relativas, convertir fechas a diferentes formatos y obtener el inicio o fin de un día específico.

    **Ejemplo de uso general**:

    .. code-block:: python

        from your_module import DateUtils

        date_utils = DateUtils()

        # Obtener una fecha relativa en formato ISO 8601
        relative_date = date_utils.get_relative_date(days=7, output_format="iso8601")
        print(relative_date)  # Devuelve la fecha dentro de 7 días en formato ISO 8601
    """

    def convert_datetime(
        self,
        datetime_value: Union[str, datetime],
        output_format: Literal[
            "iso8601",
            "iso8601_full",
            "date_only",
            "datetime",
            "timestamp_seconds",
            "timestamp_milliseconds",
            "timestamp_nanoseconds",
            "eu_format",
            "custom",
        ] = "iso8601",
        custom_format: Optional[str] = None,
        tzinfo: Optional[str] = None,
    ) -> Union[datetime, str]:
        """
        Convierte un valor de fecha/hora en diferentes formatos especificados o personalizados.

        :param datetime_value: Valor de la fecha/hora a convertir. Puede ser un `datetime` o una cadena.
        :type datetime_value: Union[str, datetime]
        :param output_format: Formato de salida deseado. Puede ser:
            - "iso8601": Formato ISO 8601 estándar (por defecto).
            - "iso8601_full": Formato ISO 8601 con microsegundos.
            - "date_only": Solo la fecha (YYYY-MM-DD).
            - "datetime": Retorna un objeto `datetime`.
            - "timestamp_seconds": Marca de tiempo en segundos desde el epoch.
            - "timestamp_milliseconds": Marca de tiempo en milisegundos desde el epoch.
            - "timestamp_nanoseconds": Marca de tiempo en nanosegundos desde el epoch.
            - "eu_format": Formato europeo (DD/MM/YYYY HH:MM:SS).
            - "custom": Usa un formato personalizado especificado en `custom_format`.
        :type output_format: Literal["iso8601", "iso8601_full", "date_only", "datetime",
                                    "timestamp_seconds", "timestamp_milliseconds",
                                    "timestamp_nanoseconds", "eu_format", "custom"]
        :param custom_format: Formato personalizado para salida si `output_format` es "custom".
                            Ejemplo: "%Y-%m-%d %H:%M:%S".
        :type custom_format: Optional[str]
        :param tzinfo: Información de zona horaria para ajustar la fecha/hora resultante.
                    Si es `None`, no se aplica ninguna zona horaria.
        :type tzinfo: Optional[str]
        :return: Fecha/hora en el formato especificado.
        :rtype: Union[datetime, str]
        :raises ValueError: Si `datetime_value` no puede ser interpretado o `output_format` es inválido.
        :raises TypeError: Si se especifica un formato personalizado sin establecer `output_format` en "custom".

        **Ejemplo de uso**:

        .. code-block:: python

            from your_module import DateUtils

            date_utils = DateUtils()

            # Convertir a ISO 8601
            iso_date = date_utils.convert_datetime("2023-01-01T12:00:00", "iso8601")
            print(iso_date)  # "2023-01-01T12:00:00Z"

            # Convertir a timestamp en milisegundos
            timestamp_ms = date_utils.convert_datetime("2023-01-01T12:00:00", "timestamp_milliseconds")
            print(timestamp_ms)  # Ejemplo: 1672531200000

            # Convertir con un formato personalizado
            custom_date = date_utils.convert_datetime(
                "2023-01-01T12:00:00", "custom", "%d-%m-%Y %H:%M:%S"
            )
            print(custom_date)  # "01-01-2023 12:00:00"
        """
        if isinstance(datetime_value, datetime):
            dt_obj = datetime_value
        elif isinstance(datetime_value, str):
            try:
                dt_obj = parse(datetime_value)
            except ValueError as e:
                raise ValueError(
                    f"No se pudo interpretar el valor de fecha/hora: '{datetime_value}'. {e}"
                ) from e
        else:
            raise TypeError(
                "El valor proporcionado debe ser un objeto `datetime` o una cadena."
            )

        if tzinfo:
            if isinstance(tzinfo, str):
                tzinfo = pytz.timezone(tzinfo)
            dt_obj = dt_obj.replace(tzinfo=tzinfo)

        if output_format == "iso8601":
            return dt_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
        elif output_format == "iso8601_full":
            return dt_obj.isoformat()
        elif output_format == "date_only":
            return dt_obj.strftime("%Y-%m-%d")
        elif output_format == "datetime":
            return dt_obj
        elif output_format == "timestamp_seconds":
            return int(dt_obj.timestamp())
        elif output_format == "timestamp_milliseconds":
            return int(dt_obj.timestamp() * 1_000)
        elif output_format == "timestamp_nanoseconds":
            return int(dt_obj.timestamp() * 1_000_000_000)
        elif output_format == "eu_format":
            return dt_obj.strftime("%d/%m/%Y %H:%M:%S")
        elif output_format == "custom":
            if not custom_format:
                raise TypeError(
                    "Debe proporcionar un formato personalizado en `custom_format` cuando `output_format` es 'custom'."
                )
            return dt_obj.strftime(custom_format)
        else:
            raise ValueError(
                f"Formato de salida '{output_format}' no soportado. Use 'iso8601', 'iso8601_full', "
                "'date_only', 'datetime', 'timestamp_seconds', 'timestamp_milliseconds', "
                "'timestamp_nanoseconds', 'eu_format', o 'custom'."
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
        output_format: Literal[
            "iso8601",
            "iso8601_full",
            "date_only",
            "datetime",
            "timestamp_seconds",
            "timestamp_milliseconds",
            "timestamp_nanoseconds",
            "eu_format",
            "custom",
        ] = "iso8601",
        custom_format: Optional[str] = None,
        tzinfo: Optional[str] = None,
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
        :param output_format: Formato de salida deseado. Puede ser:
            - "iso8601": Formato ISO 8601 estándar (por defecto).
            - "iso8601_full": Formato ISO 8601 con microsegundos.
            - "date_only": Solo la fecha (YYYY-MM-DD).
            - "datetime": Retorna un objeto `datetime`.
            - "timestamp_seconds": Marca de tiempo en segundos desde el epoch.
            - "timestamp_milliseconds": Marca de tiempo en milisegundos desde el epoch.
            - "timestamp_nanoseconds": Marca de tiempo en nanosegundos desde el epoch.
            - "eu_format": Formato europeo (DD/MM/YYYY HH:MM:SS).
            - "custom": Usa un formato personalizado especificado en `custom_format`.
        :type output_format: Literal["iso8601", "iso8601_full", "date_only", "datetime",
                                    "timestamp_seconds", "timestamp_milliseconds",
                                    "timestamp_nanoseconds", "eu_format", "custom"]
        :param custom_format: Formato personalizado para salida si `output_format` es "custom".
        :type custom_format: Optional[str]
        :param tzinfo: Información de zona horaria para ajustar la fecha/hora resultante.
                    Si es `None`, no se aplica ninguna zona horaria.
        :type tzinfo: Optional[str]
        :return: La fecha relativa en el formato especificado.
        :rtype: Union[datetime, str]

        **Ejemplo de uso**:

        .. code-block:: python

            from your_module import DateUtils
            import pytz

            date_utils = DateUtils()

            # Obtener fecha relativa con zona horaria UTC
            future_date = date_utils.get_relative_date(
                days=1, output_format="iso8601", tzinfo=pytz.UTC
            )
            print(future_date)  # "2023-01-02T00:00:00Z"

            # Obtener fecha relativa sin zona horaria
            future_date_no_tz = date_utils.get_relative_date(days=1)
            print(future_date_no_tz)  # "2023-01-02T00:00:00"
        """
        base_datetime = base_datetime or datetime.now()

        # Calcular la fecha relativa
        relative_datetime = base_datetime + relativedelta(
            months=months,
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
        )

        # Convertir al formato deseado
        return self.convert_datetime(
            relative_datetime, output_format, custom_format, tzinfo
        )

    def get_start_of_day(
        self,
        date: datetime,
        output_format: Literal["iso8601", "datetime", "custom"] = "iso8601",
        custom_format: Optional[str] = None,
    ) -> Union[str, datetime]:
        """
        Obtiene el instante inicial del día para una fecha dada.

        :param date: Fecha para la cual se obtiene el instante inicial del día.
        :type date: datetime
        :param output_format: Formato de salida deseado. Puede ser 'iso8601', 'datetime' o 'custom'.
        :type output_format: Literal["iso8601", "datetime", "custom"]
        :param custom_format: Formato personalizado para salida si `output_format` es "custom".
        :type custom_format: Optional[str]
        :return: Fecha en el formato especificado correspondiente al inicio del día.
        :rtype: Union[str, datetime]
        """
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        return self.convert_datetime(start_of_day, output_format, custom_format)

    def get_end_of_day(
        self,
        date: datetime,
        output_format: Literal["iso8601", "datetime", "custom"] = "iso8601",
        custom_format: Optional[str] = None,
    ) -> Union[str, datetime]:
        """
        Obtiene el instante final del día para una fecha dada.

        :param date: Fecha para la cual se obtiene el instante final del día.
        :type date: datetime
        :param output_format: Formato de salida deseado. Puede ser 'iso8601', 'datetime' o 'custom'.
        :type output_format: Literal["iso8601", "datetime", "custom"]
        :param custom_format: Formato personalizado para salida si `output_format` es "custom".
        :type custom_format: Optional[str]
        :return: Fecha en el formato especificado correspondiente al final del día.
        :rtype: Union[str, datetime]
        """
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=0)
        return self.convert_datetime(end_of_day, output_format, custom_format)
