"""
Este módulo proporciona la clase `InfluxdbUtils` que contiene métodos comunes para realizar operaciones
en un servidor InfluxDB. La clase incluye métodos para obtener claves de mediciones, construir consultas,
convertir fechas y escribir datos en InfluxDB.
"""

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Literal, Union

import pytz  # type: ignore
from dateutil.parser import parse  # type: ignore
from influxdb import InfluxDBClient  # type: ignore


class InfluxdbUtils:
    """
    Clase que contiene métodos comunes para realizar operaciones en un servidor InfluxDB.

    Esta clase incluye métodos para obtener claves de un measurement, construir partes de consultas,
    convertir fechas al formato ISO 8601, y escribir datos en InfluxDB.

    **Ejemplo de uso**:

    .. code-block:: python

        from ctrutils.database.influxdb import InfluxdbUtils
        from influxdb import InfluxDBClient

        client = InfluxDBClient(host="localhost", port=8086)
        utils = InfluxdbUtils()

        # Obtener las claves de un measurement agrupadas por tipo
        field_keys = utils.get_field_keys_grouped_by_type(client, "my_measurement")
        print(field_keys)
    """

    @staticmethod
    def get_field_keys_grouped_by_type(
        client: InfluxDBClient, measurement: str
    ) -> Dict[str, List[str]]:
        """
        Obtiene las claves de un measurement en un servidor InfluxDB, agrupadas por tipo de dato.

        :param client: El cliente de InfluxDB conectado al servidor.
        :type client: InfluxDBClient
        :param measurement: El nombre del measurement del que se quieren obtener las claves.
        :type measurement: str
        :return: Un diccionario con las claves del measurement agrupadas por tipo de dato.
        :rtype: Dict[str, List[str]]

        **Ejemplo de uso**:

        .. code-block:: python

            client = InfluxDBClient(host="localhost", port=8086)
            field_keys = InfluxdbUtils.get_field_keys_grouped_by_type(client, "my_measurement")
            print(field_keys)
        """
        query = f"SHOW FIELD KEYS FROM {measurement}"
        results = list(client.query(query).get_points())
        field_type_dict = defaultdict(list)

        for result in results:
            field_type_dict[result["fieldType"]].append(result["fieldKey"])

        return dict(field_type_dict)

    @staticmethod
    def build_query_fields(
        fields: Union[List[str], Dict[str, List[str]]], operation: str
    ) -> Dict[str, str]:
        """
        Construye una parte de la consulta de InfluxDB aplicando una operación a cada campo.

        :param fields: Lista de campos o diccionario donde las claves son los tipos de datos
                       y los valores son listas de campos correspondientes a ese tipo.
        :type fields: Union[List[str], Dict[str, List[str]]]
        :param operation: La operación a aplicar a cada campo (ej. MEAN, SUM).
        :type operation: str
        :return: Un diccionario donde la clave es el tipo de dato y el valor es el selector formateado.
        :rtype: Dict[str, str]

        **Ejemplo de uso**:

        .. code-block:: python

            fields = ["temperature", "humidity"]
            query_fields = InfluxdbUtils.build_query_fields(fields, "MEAN")
            print(query_fields)
        """
        query_fields = defaultdict(str)

        if isinstance(fields, list):
            query_fields["fields"] = ", ".join(
                [f'{operation}("{field}") AS "{field}"' for field in fields]
            )

        if isinstance(fields, dict):
            for field_type, field_list in fields.items():
                if field_type == "boolean" or field_type == "integer":
                    query_parts = [f'"{field}"' for field in field_list]
                else:
                    query_parts = [
                        f'{operation}("{field}") AS "{field}"'
                        for field in field_list
                    ]
                query_fields[field_type] = ", ".join(query_parts)

        return dict(query_fields)

    @staticmethod
    def convert_to_influxdb_iso(
        datetime_value: Union[str, datetime],
        output_format: Literal["default", "influxdb", "iso"] = "default",
    ) -> str:
        """
        Convierte una fecha en formato `datetime` o `str` a varios formatos, incluyendo el específico para InfluxDB.

        :param datetime_value: Valor de la fecha a convertir, puede ser una cadena o un objeto `datetime`.
        :type datetime_value: Union[str, datetime]
        :param output_format: Formato de salida deseado. Opciones disponibles:
            - "default": ISO 8601 sin microsegundos y con zona horaria UTC (actual).
            - "influxdb": Formato ISO 8601 compatible con InfluxDB (sin microsegundos y con sufijo 'Z').
            - "iso": Formato ISO 8601 completo con microsegundos.
        :type output_format: str
        :return: La fecha en el formato solicitado como string.
        :rtype: str
        :raises ValueError: Si no se puede convertir el valor al formato solicitado.
        """
        if isinstance(datetime_value, datetime):
            dt_obj = datetime_value
        elif isinstance(datetime_value, str):
            try:
                # Intentar interpretar como formato ISO 8601
                dt_obj = parse(datetime_value)
            except ValueError as e:
                raise ValueError(
                    f"Error al analizar la fecha proporcionada '{datetime_value}': {e}"
                ) from e
        else:
            raise TypeError(
                "El valor proporcionado debe ser una cadena o un objeto datetime."
            )

        # Si el datetime no tiene zona horaria, asumir que es UTC
        if dt_obj.tzinfo is None:
            dt_obj = dt_obj.replace(tzinfo=pytz.UTC)

        # Devolver el formato solicitado
        if output_format == "default":
            return dt_obj.astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%S%z")
        elif output_format == "influxdb":
            return dt_obj.astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        elif output_format == "iso":
            return dt_obj.astimezone(pytz.UTC).isoformat()
        else:
            raise ValueError(
                f"Formato de salida no soportado: '{output_format}'. Opciones disponibles: 'default', 'influxdb', 'iso'."
            )

    @staticmethod
    def convert_to_datetime(string_datetime: str) -> datetime:
        """
        Convierte una cadena que representa una fecha y hora en un objeto datetime.

        :param string_datetime: La cadena que representa la fecha y hora a convertir.
        :type string_datetime: str
        :return: Un objeto datetime con la fecha y hora correspondiente.
        :rtype: datetime

        **Ejemplo de uso**:

        .. code-block:: python

            date_obj = InfluxdbUtils.convert_to_datetime("2023-01-01T12:00:00")
            print(date_obj)  # datetime.datetime(2023, 1, 1, 12, 0)
        """
        dt_obj = parse(string_datetime)
        if not isinstance(dt_obj, datetime):
            raise ValueError(
                "El valor no pudo ser convertido a un objeto datetime."
            )
        return dt_obj

    @staticmethod
    def get_measurements_to_copy(
        client: InfluxDBClient,
    ) -> Dict[str, List[str]]:
        """
        Devuelve un diccionario que contiene las bases de datos del servidor InfluxDB remoto y sus respectivas mediciones.

        :param client: El cliente de InfluxDB remoto.
        :type client: InfluxDBClient
        :return: Un diccionario con las bases de datos como claves y una lista de mediciones como valor.
        :rtype: Dict[str, List[str]]

        **Ejemplo de uso**:

        .. code-block:: python

            client = InfluxDBClient(host="localhost", port=8086)
            databases = InfluxdbUtils.get_measurements_to_copy(client)
            print(databases)
        """
        remote_database = client.get_list_database()
        database_and_measurements = {}

        for database in remote_database:
            database_name = database["name"]
            client.switch_database(database_name)
            measurements = [m["name"] for m in client.get_list_measurements()]
            database_and_measurements[database_name] = measurements

        del database_and_measurements["_internal"]
        return database_and_measurements

    @staticmethod
    def write_measurement_check_process(
        client: InfluxDBClient,
        measurement: str,
        field: str,
        value: int,
    ) -> None:
        """
        Escribe un valor en una medición especificada en InfluxDB.

        :param client: El cliente de InfluxDB que se va a utilizar para escribir los datos.
        :type client: InfluxDBClient
        :param measurement: El nombre de la medición en la que se va a escribir el valor.
        :type measurement: str
        :param field: El nombre del campo en el que se va a escribir el valor.
        :type field: str
        :param value: El valor a escribir en el campo.
        :type value: int

        **Ejemplo de uso**:

        .. code-block:: python

            client = InfluxDBClient(host="localhost", port=8086)
            InfluxdbUtils.write_measurement_check_process(client, "my_measurement", "status", 1)
        """
        json_body = [
            {
                "measurement": measurement,
                "fields": {field: value},
            }
        ]
        client.write_points(points=json_body)
