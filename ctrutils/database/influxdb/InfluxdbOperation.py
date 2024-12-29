"""
Este modulo proporciona la clase `InfluxdbOperation` para manejar operaciones en una base de datos
InfluxDB utilizando un cliente `InfluxDBClient`. La clase incluye metodos para cambiar de base de datos,
ejecutar consultas, escribir datos en InfluxDB, y formatear valores para escritura.
"""

from typing import Any, Optional, Union

import pandas as pd  # type: ignore

from ctrutils.database.influxdb.InfluxdbConnection import InfluxdbConnection
from ctrutils.utils.DateUtils import DateUtils


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
        self._date_utils = DateUtils()

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
        tags: Optional[dict] = None,
        clean_previous: bool = False,
    ) -> None:
        """
        Escribe una lista de puntos directamente en InfluxDB, con soporte para la actualizacion de registros mediante tags.

        Este metodo permite escribir una lista de puntos en InfluxDB. Si se proporciona el parametro `tags`, estos se
        aplicaran como tags adicionales o sobrescribirán los existentes en cada punto. Adicionalmente, si se establece
        el parametro `clean_previous` como `True`, se eliminaran los registros existentes con tags que no coincidan con los
        proporcionados antes de escribir los nuevos puntos.

        :param points: Lista de puntos a escribir en InfluxDB. Cada punto debe incluir al menos las claves
            `measurement`, `time`, y `fields`. Los tags son opcionales, pero pueden incluirse para clasificar los puntos.
        :type points: list
        :param database: El nombre de la base de datos en la que se escribiran los puntos. Si no se especifica,
            se utilizara la base de datos activa.
        :type database: Optional[str]
        :param tags: Diccionario de tags adicionales a agregar o sobrescribir en los puntos proporcionados.
        :type tags: Optional[dict]
        :param clean_previous: Si es True, elimina registros conflictivos antes de escribir los nuevos puntos.
            Los registros conflictivos son aquellos con el mismo `time` pero cuyos tags no coinciden con los
            proporcionados en los nuevos puntos. Por defecto es False.
        :type clean_previous: bool
        :raises ValueError:
            - Si no se proporciona una lista de puntos valida.
            - Si no se especifica una base de datos valida.

        **Ejemplo de uso basico**:

        .. code-block:: python

            points = [
                {"measurement": "test_tags", "time": "2023-01-01T00:00:00", "fields": {"value": 10}},
                {"measurement": "test_tags", "time": "2023-01-01T01:00:00", "fields": {"value": 20}}
            ]

            influxdb_op.write_points(points=points, database="test_db")

        **Ejemplo con tags adicionales**:

        .. code-block:: python

            points = [
                {"measurement": "test_tags", "time": "2023-01-01T00:00:00", "fields": {"value": 10}, "tags": {"sensor": "A"}},
                {"measurement": "test_tags", "time": "2023-01-01T01:00:00", "fields": {"value": 20}, "tags": {"sensor": "B"}}
            ]

            influxdb_op.write_points(points=points, database="test_db", tags={"location": "site_1"})

            # Esto agregara el tag "location: site_1" a ambos puntos.

        **Ejemplo de actualizacion de registros con tags**:

        .. code-block:: python

            points = [
                {"measurement": "test_tags", "time": "2023-01-01T00:00:00", "fields": {"value": 10}, "tags": {"sensor": "A"}},
                {"measurement": "test_tags", "time": "2023-01-01T01:00:00", "fields": {"value": 20}, "tags": {"sensor": "B"}}
            ]

            # Escribir puntos iniciales
            influxdb_op.write_points(points=points, database="test_db")

            # Actualizar el tag "sensor" para el segundo punto
            updated_points = [
                {"measurement": "test_tags", "time": "2023-01-01T01:00:00", "fields": {"value": 20}, "tags": {"sensor": "C"}}
            ]

            influxdb_op.write_points(points=updated_points, database="test_db", clean_previous=True)

            # Esto eliminara el registro original con "sensor: B" y escribira el nuevo con "sensor: C".
        """
        db_to_use = database or self._database
        if db_to_use is None:
            raise ValueError(
                "Debe proporcionar una base de datos o establecerla mediante el metodo 'switch_database'."
            )
        self.switch_database(db_to_use)

        if not points:
            raise ValueError("La lista de puntos no puede estar vacia.")

        # Agregar tags adicionales a los puntos
        if tags:
            for point in points:
                point["tags"] = {**point.get("tags", {}), **tags}

        if clean_previous:
            # Eliminar registros conflictivos
            for point in points:
                measurement = point.get("measurement")
                time = self._date_utils.convert_datetime(
                    datetime_value=point.get("time"), output_format="iso8601"
                )
                point_tags = point.get("tags", {})

                if not measurement or not time:
                    raise ValueError(
                        "Todos los puntos deben especificar 'measurement' y 'time'."
                    )

                # Construir consulta para eliminar solo registros conflictivos
                tag_filter = " OR ".join(
                    [f"{key}!='{value}'" for key, value in point_tags.items()]
                )
                delete_query = (
                    f"DELETE FROM {measurement} WHERE time = '{time}'"
                )
                if tag_filter:
                    delete_query += f" AND {tag_filter}"

                self._client.query(delete_query, database=db_to_use)

        # Escribir los puntos
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
        clean_previous_tags: bool = False,
    ) -> None:
        """
        Convierte un DataFrame en una lista de puntos y los escribe en InfluxDB, con soporte para la gestion de tags.

        Este metodo toma un DataFrame de pandas y lo convierte en una lista de puntos para escribir en InfluxDB.
        Los valores NaN en el DataFrame seran excluidos de los puntos generados. Si se especifica el parametro `tags`,
        estos se agregaran como tags adicionales a cada punto. Adicionalmente, si se establece `clean_previous_tags` como
        `True`, se eliminaran los registros existentes que no coincidan con los nuevos tags antes de escribir los puntos.

        :param measurement: Nombre de la medida en InfluxDB.
        :type measurement: str
        :param data: DataFrame de pandas con los datos a convertir. El indice debe ser de tipo datetime.
        :type data: pd.DataFrame
        :param tags: Diccionario de tags a asociar a los puntos generados.
        :type tags: Optional[dict]
        :param database: El nombre de la base de datos en la que se escribiran los puntos. Si no se especifica,
            se utilizara la base de datos activa.
        :type database: Optional[str]
        :param pass_to_float: Si es True, convierte valores int y bool a float antes de escribirlos en InfluxDB. Por defecto es True.
        :type pass_to_float: bool
        :param convert_bool_to_float: Si es True, duplica las columnas de tipo bool y las convierte a float. Por defecto es False.
        :type convert_bool_to_float: bool
        :param suffix_bool_to_float: Sufijo de las nuevas columnas de tipo float provenientes de columnas de tipo bool.
        :type suffix_bool_to_float: str
        :param clean_previous_tags: Si es True, elimina los puntos existentes que no coincidan con los nuevos tags antes
            de escribir los puntos generados. Por defecto es False.
        :type clean_previous_tags: bool
        :raises ValueError:
            - Si no se proporciona un DataFrame o un nombre de medida valido.
            - Si el indice del DataFrame no es convertible a un indice de tipo datetime.

        **Ejemplo de uso basico**:

        .. code-block:: python

            import pandas as pd

            data = pd.DataFrame({
                "value": [10, 20, None, 40],
                "sensor": ["A", "B", "C", "D"]
            }, index=pd.date_range(start="2023-01-01", periods=4, freq="H"))

            influxdb_op.write_dataframe(
                measurement="test_tags",
                data=data,
                database="test_db"
            )

        **Ejemplo con tags adicionales**:

        .. code-block:: python

            influxdb_op.write_dataframe(
                measurement="test_tags",
                data=data,
                tags={"location": "site_1"},
                database="test_db"
            )

            # Esto agregara el tag "location: site_1" a todos los puntos generados.

        **Ejemplo de actualizacion de registros con tags**:

        .. code-block:: python

            influxdb_op.write_dataframe(
                measurement="test_tags",
                data=data,
                tags={"location": "updated_site"},
                database="test_db",
                clean_previous_tags=True
            )

            # Esto eliminara los registros que no coincidan con los nuevos tags y actualizara los puntos existentes.
        """
        if data is None or measurement is None:
            raise ValueError(
                "Debe proporcionar un DataFrame 'data' y un 'measurement'."
            )

        # Seleccionar las columnas booleanas y convertirlas a float si es necesario
        if convert_bool_to_float:
            for column in data.select_dtypes(include=["bool"]).columns:
                data[f"{column}{suffix_bool_to_float}"] = data[column].astype(
                    float
                )

        # Crear lista de puntos a partir del DataFrame
        points = []
        for index, row in data.iterrows():
            fields = {
                field: (
                    self.normalize_value_to_write(value)
                    if pass_to_float
                    else value
                )
                for field, value in row.items()
                if pd.notna(value)
            }
            if fields:
                point = {
                    "measurement": measurement,
                    "time": self._date_utils.convert_datetime(
                        datetime_value=index, output_format="iso8601"
                    ),
                    "fields": fields,
                }
                points.append(point)

        # Delegar la escritura a write_points
        self.write_points(
            points=points,
            database=database,
            tags=tags,
            clean_previous=clean_previous_tags,
        )
