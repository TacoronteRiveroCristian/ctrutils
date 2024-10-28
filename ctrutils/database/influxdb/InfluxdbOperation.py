"""
Este módulo proporciona la clase `InfluxdbOperation` para manejar operaciones en una base de datos
InfluxDB utilizando un cliente `InfluxDBClient`. La clase incluye métodos para cambiar de base de datos,
ejecutar consultas, escribir datos en InfluxDB, y formatear valores para escritura.
"""

from typing import Any, Optional, Union

import pandas as pd

from ctrutils.database.influxdb.InfluxdbConnection import InfluxdbConnection
from ctrutils.database.influxdb.InfluxdbUtils import InfluxdbUtils


class InfluxdbOperation(InfluxdbConnection):
    """
    Clase para manejar operaciones en la base de datos InfluxDB con un cliente `InfluxDBClient`.

    Esta clase hereda de `InfluxdbConnection` y proporciona métodos adicionales para realizar
    consultas, escribir puntos en la base de datos, y cambiar la base de datos de trabajo.

    **Ejemplo de uso**:

    .. code-block:: python

        from ctrutils.database.influxdb import InfluxdbOperation

        # Crear una conexión y realizar operaciones en InfluxDB
        influxdb_op = InfluxdbOperation(host="localhost", port=8086, timeout=10)

        # Cambiar la base de datos activa
        influxdb_op.switch_database("mi_base_de_datos")

        # Ejecutar una consulta y obtener resultados en DataFrame
        query = "SELECT * FROM my_measurement LIMIT 10"
        data = influxdb_op.get_data(query=query)
        print(data)

        # Escribir datos en InfluxDB
        influxdb_op.write_points(measurement="my_measurement", data=data)

    :param host: La dirección del host de InfluxDB.
    :type host: str
    :param port: El puerto de conexión a InfluxDB.
    :type port: Union[int, str]
    :param timeout: El tiempo de espera para la conexión en segundos. Por defecto es 5 segundos.
    :type timeout: Optional[Union[int, float]]
    :param kwargs: Parámetros adicionales para la conexión a InfluxDB.
    :type kwargs: Any
    """

    def __init__(
        self,
        host: str,
        port: Union[int, str],
        timeout: Optional[Union[int, float]] = 5,
        **kwargs: Any,
    ):
        """
        Inicializa la clase `InfluxdbOperation` y establece una conexión con InfluxDB.

        :param host: La dirección del host de InfluxDB.
        :type host: str
        :param port: El puerto de conexión a InfluxDB.
        :type port: Union[int, str]
        :param timeout: El tiempo de espera para la conexión en segundos. Por defecto es 5 segundos.
        :type timeout: Optional[Union[int, float]]
        :param kwargs: Parámetros adicionales para la conexión a InfluxDB.
        :type kwargs: Any
        """
        super().__init__(host=host, port=port, timeout=timeout, **kwargs)
        self._client = self.get_client
        self._database: Optional[str] = None
        self._influxdb_utils = InfluxdbUtils()

    def switch_database(self, database: str) -> None:
        """
        Cambia la base de datos activa en el cliente de InfluxDB.

        :param database: Nombre de la base de datos a utilizar.
        :type database: str
        :return: None

        **Ejemplo de uso**:

        .. code-block:: python

            influxdb_op = InfluxdbOperation(host="localhost", port=8086)
            influxdb_op.switch_database("mi_base_de_datos")
        """
        if database not in self._client.get_list_database():
            self._client.create_database(database)
        self._database = database
        self._client.switch_database(database)

    def get_data(
        self,
        query: str,
        database: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Ejecuta una consulta en InfluxDB y devuelve los resultados en un DataFrame.

        :param query: Query a ejecutar en InfluxDB.
        :type query: str
        :param database: Nombre de la base de datos en InfluxDB. Si no se especifica, utiliza la base de datos activa.
        :type database: Optional[str]
        :return: DataFrame con los resultados de la consulta.
        :rtype: pd.DataFrame
        :raises ValueError: Si no se encuentran datos.

        **Ejemplo de uso**:

        .. code-block:: python

            influxdb_op = InfluxdbOperation(host="localhost", port=8086)
            influxdb_op.switch_database("mi_base_de_datos")
            query = "SELECT * FROM my_measurement LIMIT 10"
            data = influxdb_op.get_data(query=query)
            print(data)
        """
        db_to_use = database or self._database
        if db_to_use is None:
            raise ValueError(
                "Debe proporcionar una base de datos o establecerla mediante el método 'switch_database'."
            )
        self.switch_database(db_to_use)

        result_set = self._client.query(query=query, chunked=True, chunk_size=5000)
        data_list = [point for chunk in result_set for point in chunk.get_points()]

        if not data_list:
            raise ValueError(
                f"No hay datos disponibles para la query '{query}' en la base de datos '{database or self._database}'."
            )

        df = pd.DataFrame(data_list)
        if "time" in df.columns:
            df = df.set_index("time")

        return df

    def check_value_format_to_write(self, value: Any) -> bool:
        """
        Verifica si el valor es adecuado para ser escrito en InfluxDB.

        :param value: Valor a verificar.
        :type value: Any
        :return: `True` si el valor es válido para escritura, `False` en caso contrario.
        :rtype: bool

        **Ejemplo de uso**:

        .. code-block:: python

            influxdb_op = InfluxdbOperation(host="localhost", port=8086)
            is_valid = influxdb_op.check_value_format_to_write(42)
            print(is_valid)  # True
        """
        return not (value is None or pd.isna(value))

    def normalize_value_to_write(self, value: Any) -> Any:
        """
        Normaliza el valor para su escritura en InfluxDB.

        :param value: Valor a normalizar.
        :type value: Any
        :return: El valor normalizado.
        :rtype: Any

        **Ejemplo de uso**:

        .. code-block:: python

            influxdb_op = InfluxdbOperation(host="localhost", port=8086)
            normalized_value = influxdb_op.normalize_value_to_write(42)
            print(normalized_value)  # 42.0
        """
        if isinstance(value, bool):
            return value
        elif isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            return value
        else:
            return value

    def write_points(
        self,
        measurement: Optional[str] = None,
        data: Optional[pd.DataFrame] = None,
        points: Optional[list] = None,
        database: Optional[str] = None,
        tags: Optional[dict] = None,
    ) -> None:
        """
        Escribe datos en InfluxDB desde un DataFrame o una lista de puntos.

        :param measurement: Nombre de la medida en InfluxDB. Obligatorio si se proporciona un DataFrame.
        :type measurement: Optional[str]
        :param data: DataFrame de pandas con los datos a escribir en InfluxDB.
        :type data: Optional[pd.DataFrame]
        :param points: Lista de puntos a escribir directamente en InfluxDB. Si se proporciona, `data` no es necesario.
        :type points: Optional[list]
        :param database: El nombre de la base de datos en la que se escribirán los datos.
        :type database: Optional[str]
        :param tags: Diccionario de tags a asociar a los datos.
        :type tags: Optional[dict]
        :raises ValueError: Si no se proporciona ni `data` ni `points`.

        **Ejemplo de uso**:

        .. code-block:: python

            influxdb_op = InfluxdbOperation(host="localhost", port=8086)
            influxdb_op.switch_database("mi_base_de_datos")

            # Crear un DataFrame para escribir en InfluxDB
            data = pd.DataFrame({
                "time": pd.date_range(start="2023-01-01", periods=5, freq="D"),
                "value": [10, 20, 30, 40, 50]
            })
            data.set_index("time", inplace=True)

            influxdb_op.write_points(measurement="my_measurement", data=data)
        """
        db_to_use = database or self._database
        if db_to_use is None:
            raise ValueError(
                "Debe proporcionar una base de datos o establecerla mediante el método 'switch_database'."
            )
        self.switch_database(db_to_use)

        if points is None:
            if data is None or measurement is None:
                raise ValueError(
                    "Debe proporcionar un DataFrame 'data' y un 'measurement' o una lista de 'points'."
                )

            if "time" not in data.columns:
                data["time"] = pd.to_datetime(data.index, format="mixed")
            points = data.to_dict(orient="records")

            points_list = []
            for record in points:
                point = {
                    "time": self._influxdb_utils.convert_to_influxdb_iso(
                        record.pop("time")
                    ),
                    "fields": {
                        field: self.normalize_value_to_write(value)
                        for field, value in record.items()
                    },
                    "measurement": measurement,
                }
                if tags:
                    point["tags"] = tags

                if point["fields"]:
                    points_list.append(point)
        else:
            points_list = points

        self._client.write_points(
            points=points_list, database=database, batch_size=5000
        )
