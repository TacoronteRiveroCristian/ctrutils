"""
Este módulo proporciona la clase `InfluxdbConnection` para manejar la conexión
a una base de datos InfluxDB mediante un único cliente `InfluxDBClient`. La clase
permite establecer la conexión, obtener información del cliente, y cerrar la conexión.
"""

from typing import Any, Dict, Optional, Union

from influxdb import InfluxDBClient


class InfluxdbConnection:
    """
    Clase para manejar la conexión a la base de datos InfluxDB con un único cliente `InfluxDBClient`.

    Esta clase permite establecer una conexión con InfluxDB, obtener información del cliente y
    cerrar la conexión cuando ya no sea necesaria. Para manejar múltiples clientes, se pueden crear
    múltiples instancias de esta clase.

    **Ejemplo de uso**:

    .. code-block:: python

        from ctrutils.database.influxdb import InfluxdbConnection

        # Crear una conexión a InfluxDB
        influxdb_connection = InfluxdbConnection(host="localhost", port=8086, timeout=10)

        # Obtener el cliente y su información
        client_info = influxdb_connection.get_client_info
        print(client_info)

        # Cerrar la conexión
        influxdb_connection.close_client

    :param host: Host de InfluxDB.
    :type host: str
    :param port: Puerto de InfluxDB.
    :type port: Union[int, str]
    :param timeout: Tiempo de espera en segundos para la conexión (por defecto es 5).
    :type timeout: Optional[Union[int, float]], optional
    :param kwargs: Parámetros adicionales para el cliente InfluxDB.
    :type kwargs: Any
    """

    def __init__(
        self,
        host: str,
        port: Union[int, str],
        timeout: Optional[Union[int, float]] = 5,
        **kwargs: Any,
    ) -> None:
        """
        Inicializa una conexión a InfluxDB.

        Este método configura el cliente `InfluxDBClient` con los parámetros proporcionados,
        y permite añadir parámetros adicionales a través de `kwargs`.

        :param host: Host de InfluxDB.
        :type host: str
        :param port: Puerto de InfluxDB.
        :type port: Union[int, str]
        :param timeout: Tiempo de espera en segundos para la conexión (por defecto es 5).
        :type timeout: Optional[Union[int, float]], optional
        :param kwargs: Parámetros adicionales para el cliente InfluxDB.
        :type kwargs: Any
        """
        self.host = host
        self.port = port
        self.database = None
        self.timeout = timeout
        self._headers = {"Accept": "application/json"}
        self._gzip = True

        # Crear el cliente de InfluxDB
        self.client = InfluxDBClient(
            host=host,
            port=port,
            timeout=timeout,
            headers=self._headers,
            gzip=self._gzip,
            **kwargs,
        )

    @property
    def get_client_info(self) -> Dict[str, Any]:
        """
        Obtiene información del cliente actual.

        :return: Un diccionario con la información del cliente, incluyendo host, puerto,
                 base de datos, tiempo de espera, headers y compresión gzip.
        :rtype: Dict[str, Any]

        **Ejemplo de uso**:

        .. code-block:: python

            influxdb_connection = InfluxdbConnection(host="localhost", port=8086)
            client_info = influxdb_connection.get_client_info
            print(client_info)
        """
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "timeout": self.timeout,
            "headers": self._headers,
            "gzip": self._gzip,
        }

    @property
    def get_client(self) -> InfluxDBClient:
        """
        Obtiene el cliente actual `InfluxDBClient`.

        :return: El cliente actual de tipo `InfluxDBClient`.
        :rtype: InfluxDBClient

        **Ejemplo de uso**:

        .. code-block:: python

            influxdb_connection = InfluxdbConnection(host="localhost", port=8086)
            client = influxdb_connection.get_client
            print(client)  # Muestra el cliente InfluxDBClient actual
        """
        return self.client

    @property
    def close_client(self) -> None:
        """
        Cierra la conexión actual del cliente `InfluxDBClient`.

        **Ejemplo de uso**:

        .. code-block:: python

            influxdb_connection = InfluxdbConnection(host="localhost", port=8086)
            influxdb_connection.close_client  # Cierra la conexión
        """
        self.client.close()
