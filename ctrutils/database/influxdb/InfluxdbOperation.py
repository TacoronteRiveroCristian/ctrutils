"""
Este modulo proporciona la clase `InfluxdbOperation` para manejar operaciones en una base de datos
InfluxDB utilizando un cliente `InfluxDBClient`. La clase incluye metodos para cambiar de base de datos,
ejecutar consultas, escribir datos en InfluxDB, y formatear valores para escritura.
"""

from typing import Any, Optional, Union

import pandas as pd

from ctrutils.database.influxdb.InfluxdbConnection import InfluxdbConnection
from ctrutils.database.influxdb.InfluxdbUtils import InfluxdbUtils


class InfluxdbOperation(InfluxdbConnection):
    """
    Clase para manejar operaciones en la base de datos InfluxDB con un cliente `InfluxDBClient`.

    Esta clase hereda de `InfluxdbConnection` y proporciona metodos adicionales para realizar
    consultas, escribir puntos en la base de datos, y cambiar la base de datos de trabajo.

    **Ejemplo de uso**:

    .. code-block:: python

        from ctrutils.database.influxdb import InfluxdbOperation

        # Crear una conexion y realizar operaciones en InfluxDB
        influxdb_op = InfluxdbOperation(host="localhost", port=8086, timeout=10)

        # Cambiar la base de datos activa
        influxdb_op.switch_database("mi_base_de_datos")

        # Ejecutar una consulta y obtener resultados en DataFrame
        query = "SELECT * FROM my_measurement LIMIT 10"
        data = influxdb_op.get_data(query=query)
        print(data)

        # Escribir datos en InfluxDB
        influxdb_op.write_points(measurement="my_measurement", data=data)

    :param host: La direccion del host de InfluxDB.
    :type host: str
    :param port: El puerto de conexion a InfluxDB.
    :type port: Union[int, str]
    :param timeout: El tiempo de espera para la conexion en segundos. Por defecto es 5 segundos.
    :type timeout: Optional[Union[int, float]]
    :param kwargs: Parametros adicionales para la conexion a InfluxDB.
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
        Inicializa la clase `InfluxdbOperation` y establece una conexion con InfluxDB.

        :param host: La direccion del host de InfluxDB.
        :type host: str
        :param port: El puerto de conexion a InfluxDB.
        :type port: Union[int, str]
        :param timeout: El tiempo de espera para la conexion en segundos. Por defecto es 5 segundos.
        :type timeout: Optional[Union[int, float]]
        :param kwargs: Parametros adicionales para la conexion a InfluxDB.
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
                "Debe proporcionar una base de datos o establecerla mediante el metodo 'switch_database'."
            )
        self.switch_database(db_to_use)

        result_set = self._client.query(
            query=query, chunked=True, chunk_size=5000
        )
        data_list = [
            point for chunk in result_set for point in chunk.get_points()
        ]

        if not data_list:
            raise ValueError(
                f"No hay datos disponibles para la query '{query}' en la base de datos '{database or self._database}'."
            )

        df = pd.DataFrame(data_list)
        if "time" in df.columns:
            df = df.set_index("time")

        # Asegurarse de que el indice sea de tipo datetime
        df.index = pd.to_datetime(df.index)

        return df

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
        if isinstance(value, int):
            return float(value)
        elif isinstance(value, float):
            return value
        else:
            return value

    def write_points(
        self,
        points: list,
        database: Optional[str] = None,
    ) -> None:
        """
        Escribe una lista de puntos directamente en InfluxDB.

        :param points: Lista de puntos a escribir en InfluxDB.
        :type points: list
        :param database: El nombre de la base de datos en la que se escribiran los datos.
        :type database: Optional[str]
        :raises ValueError: Si no se proporciona una lista de puntos.

        **Ejemplo de uso**:

        .. code-block:: python

            influxdb_op = InfluxdbOperation(host="localhost", port=8086)
            influxdb_op.switch_database("mi_base_de_datos")

            points = [
                {"measurement": "my_measurement", "fields": {"value": 10}, "time": "2023-01-01T00:00:00Z"},
                {"measurement": "my_measurement", "fields": {"value": 20}, "time": "2023-01-02T00:00:00Z"}
            ]

            influxdb_op.write_points(points=points)
        """
        db_to_use = database or self._database
        if db_to_use is None:
            raise ValueError(
                "Debe proporcionar una base de datos o establecerla mediante el metodo 'switch_database'."
            )
        self.switch_database(db_to_use)

        if not points:
            raise ValueError("La lista de puntos no puede estar vacia.")

        self._client.write_points(
            points=points, database=db_to_use, batch_size=5000
        )

    def write_dataframe(
        self,
        measurement: str,
        data: pd.DataFrame,
        tags: Optional[dict] = None,
        database: Optional[str] = None,
        pass_to_float: bool = True,
        convert_bool_to_float: bool = False,
        suffix_bool_to_float: str = "_bool_to_float",
    ) -> list:
        """
        Convierte un DataFrame en una lista de puntos en el formato adecuado para escribir en InfluxDB.

        :param measurement: Nombre de la medida en InfluxDB.
        :type measurement: str
        :param data: DataFrame de pandas con los datos a convertir.
        :type data: pd.DataFrame
        :param tags: Diccionario de tags a asociar a los puntos.
        :type tags: Optional[dict]
        :param database: El nombre de la base de datos en la que se escribirán los datos.
        :type database: Optional[str]
        :param pass_to_float: Si es True, convierte valores int y bool a float antes de escribirlos en InfluxDB. Por defecto es True.
        :type pass_to_float: bool
        :param convert_bool_to_float: Si es True, duplica las columnas de tipo bool y las convierte a float. Por defecto es False.
        :type convert_bool_to_float: bool
        :param suffix_bool_to_float: Sufijo de las nuevas columnas de tipo float provenientes de columnas de tipo bool.
        :type suffix_bool_to_float: str
        :return: Lista de puntos formateados para InfluxDB.
        :rtype: list
        :raises ValueError:
            - Si no se proporciona un DataFrame o el nombre de la medida.
            - ValueError: Si el índice del DataFrame no es convertible a un índice de tipo datetime.

        **Notas**:
            - El índice del DataFrame debe ser de tipo datetime para garantizar la compatibilidad con InfluxDB.
            - Los valores NaN serán excluidos al convertir los datos a puntos.

        **Ejemplo de uso**:

        .. code-block:: python

            import pandas as pd
            from influxdb_client import InfluxdbOperation

            influxdb_op = InfluxdbOperation(host="localhost", port=8086)

            data = pd.DataFrame({
                "value": [10, 20, None, 40, 50],
                "other_field": [True, False, None, True, False]
            }, index=pd.date_range(start="2023-01-01", periods=5, freq="D"))

            points = influxdb_op.write_dataframe(
                measurement="my_measurement",
                data=data,
                tags={"location": "test_site"}
            )
            print(points)
        """

        # Comprobar que se proporcionaron los argumentos necesarios
        if data is None or measurement is None:
            raise ValueError(
                "Debe proporcionar un DataFrame 'data' y un 'measurement'."
            )

        # Seleccionar las columnas booleanas y pasarlas a float si es necesario
        if convert_bool_to_float:
            for c in data.select_dtypes(include=["bool"]).columns:
                data[f"{c}{suffix_bool_to_float}"] = data[c].astype(float)

        # Crear lista de puntos a partir del dataframe
        points = []
        for index, row in data.iterrows():
            # Filtrar los campos validos: excluir NaN y valores no soportados
            fields = {
                field: (
                    self.normalize_value_to_write(value)
                    if pass_to_float
                    else value
                )
                for field, value in row.items()
                if pd.notna(value)
            }

            # Solo agregar el punto si tiene campos validos
            if fields:
                point = {
                    "time": self._influxdb_utils.convert_to_influxdb_iso(index),
                    "fields": fields,
                    "measurement": measurement,
                }
                if tags:
                    point["tags"] = tags
                points.append(point)

        # Registar lista de puntos
        self.write_points(points=points, database=database)
