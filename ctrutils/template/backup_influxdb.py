"""
Este modulo contiene la clase `BackupInfluxdb`, que permite realizar una copia completa de todas las bases de datos
de un servidor remoto de InfluxDB hacia un servidor local de InfluxDB. La clase gestiona la conexion
con los servidores de origen y destino y utiliza consultas para copiar solo los datos que no esten
presentes en el servidor de destino, optimizando el proceso de transferencia.

Uso:
    Ejecuta este modulo directamente para iniciar el proceso de copia de bases de datos:

    ```bash
    python influxdb_backup_template.py
    ```
"""

from typing import Dict, List, Optional, Union

from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from ctrutils.database.influxdb.InfluxdbUtils import InfluxdbUtils
from ctrutils.handlers.ErrorHandlerBase import ErrorHandler
from ctrutils.handlers.LoggingHandlerBase import LoggingHandler

# Ruta del fichero de logs
LOG_FILE = "/path/to/backup_to_delphos.log"

# Configuracion del cliente InfluxDB de origen
INFLUXDB_SOURCE: Dict[str, Union[str, int]] = {
    "host": "localhost",
    "port": 8086,
}

INFLUXDB_DESTINATION: Dict[str, Union[str, int]] = {
    "host": "localhost",
    "port": 8087,
}


class BackupInfluxdb:
    """
    Clase para copiar todas las bases de datos de un servidor remoto de InfluxDB a un servidor de destino.

    Esta clase gestiona la conexion con los servidores de origen y destino, obtiene las bases de datos y mediciones
    que deben copiarse, y realiza la transferencia de los datos.

    :ivar logger: Manejador de logs para registrar eventos del proceso.
    :vartype logger: logging.Logger
    :ivar error: Manejador de errores para gestionar excepciones y registrar fallos.
    :vartype error: ErrorHandler
    :ivar influx_utils: Utilidades para operaciones con InfluxDB.
    :vartype influx_utils: InfluxdbUtils
    :ivar source_client: Cliente de InfluxDB para el servidor de origen.
    :vartype source_client: Optional[InfluxdbOperation]
    :ivar destination_client: Cliente de InfluxDB para el servidor de destino.
    :vartype destination_client: Optional[InfluxdbOperation]
    :ivar databases_and_measurements_to_copy: Diccionario con las bases de datos y sus mediciones a copiar.
    :vartype databases_and_measurements_to_copy: Optional[Dict[str, List[str]]]
    """

    def __init__(self) -> None:
        """
        Inicializa la clase BackupInfluxdb y configura los manejadores de logs y errores,
        asi como las utilidades de InfluxDB.
        """
        self.logger = LoggingHandler().configure_logger(
            name=self.__class__.__name__,
            log_file=LOG_FILE,
        )
        self.error = ErrorHandler()
        self.influx_utils = InfluxdbUtils()

        self.logger.info(f"Clase '{self.__class__.__name__}' inicializada.")

        self.source_client: Optional[InfluxdbOperation] = None
        self.destination_client: Optional[InfluxdbOperation] = None
        self.databases_and_measurements_to_copy: Optional[Dict[str, List[str]]] = None

    def setup_clients(self) -> None:
        """
        Configura los clientes de InfluxDB para el servidor de origen y de destino.

        :raises Exception: Si ocurre un error al crear los clientes.
        """
        self.logger.info("Creando clientes InfluxDB...")

        # Intenta crear los clientes de origen y destino
        try:
            self.source_client = InfluxdbOperation(
                host=str(INFLUXDB_SOURCE["host"]),
                port=int(INFLUXDB_SOURCE["port"]),
            )
            self.destination_client = InfluxdbOperation(
                host=str(INFLUXDB_DESTINATION["host"]),
                port=int(INFLUXDB_DESTINATION["port"]),
            )
        except Exception:
            txt_error = "Error al crear los clientes."
            self.error.throw_error(txt_error, self.logger)
        else:
            if self.source_client and self.destination_client:
                self.logger.info(
                    f"Clientes creados: {self.source_client.get_client_info} | "
                    f"{self.destination_client.get_client_info}"
                )

    def get_measurements_to_copy(self) -> None:
        """
        Obtiene las bases de datos y mediciones que deben copiarse desde el servidor remoto.
        """
        self.logger.info("Obteniendo mediciones a copiar del servidor remoto...")

        if self.source_client:
            remote_client = self.source_client.get_client  # Cliente remoto
            self.databases_and_measurements_to_copy = (
                self.influx_utils.get_measurements_to_copy(remote_client)
            )
            self.logger.info(
                f"Mediciones a copiar: {self.databases_and_measurements_to_copy}"
            )
        else:
            self.logger.error("Cliente de origen no inicializado.")

    def get_selectors_to_do_average(self, measurement: str) -> Dict[str, str]:
        """
        Obtiene las claves necesarias de un measurement para realizar la media de las variables.

        :param measurement: Nombre de la medicion.
        :return: Diccionario con las claves para realizar la consulta de media.
        """
        if self.source_client:
            remote_client = self.source_client.get_client
            fields = self.influx_utils.get_field_keys_grouped_by_type(
                remote_client, measurement
            )
            selectors = self.influx_utils.build_query_fields(fields, "MEAN")
            return selectors
        else:
            raise ValueError("Cliente de origen no inicializado")

    def check_if_data_already_exists(self, measurement: str) -> Optional[str]:
        """
        Comprueba si ya existen datos en el servidor destino para evitar duplicados.

        :param measurement: Nombre de la medicion.
        :return: Última fecha/hora registrada en el servidor destino, o None si no existen datos.
        """
        if not self.destination_client:
            raise ValueError("Cliente de destino no inicializado")

        query = f"""
        SELECT *
        FROM {measurement}
        WHERE time <= now()
        ORDER BY time DESC
        LIMIT 1
        """
        try:
            data = self.destination_client.get_data(query)
            index = (
                data.index[0] if data is not None and hasattr(data, "index") else None
            )
            return str(index) if index else None
        except ValueError:
            return None

    def build_queries(self, selectors: Dict[str, str], measurement: str) -> List[str]:
        """
        Construye las consultas para la copia de los datos.

        :param selectors: Claves y operaciones para los campos a copiar.
        :param measurement: Nombre de la medicion.
        :return: Lista de consultas SQL para obtener y copiar los datos.
        """
        querys = []
        query_start_datetime = ""
        start_datetime = self.check_if_data_already_exists(measurement)
        if start_datetime:
            query_start_datetime += f"WHERE time >= '{start_datetime}'"

        for type_selector, selector in selectors.items():
            group_by_clause = "GROUP BY time(5m)" if type_selector != "boolean" else ""
            query = f"""
            SELECT {selector}
            FROM "{measurement}"
            {query_start_datetime}
            {group_by_clause}
            """
            querys.append(query)
        return querys

    def read_and_write_data(self, querys: List[str], measurement: str) -> None:
        """
        Lee datos del servidor de origen y los escribe en el servidor de destino.

        :param querys: Lista de consultas SQL para obtener los datos.
        :param measurement: Nombre de la medicion donde se almacenaran los datos.
        """
        if self.source_client and self.destination_client:
            for index, query in enumerate(querys, start=1):
                self.logger.info(f"\t\t\tObteniendo datos de la consulta nº {index}...")
                try:
                    data = self.source_client.get_data(query)
                    self.destination_client.write_points(measurement, data)
                    self.logger.info(f"\t\t\t\t{len(data)} registro/s escritos.")
                except Exception:
                    txt_error = "Error al obtener o escribir los datos."
                    self.error.throw_error(txt_error, self.logger)
        else:
            self.logger.error("Clientes de InfluxDB no inicializados.")

    def copy_databases(self) -> None:
        """
        Copia las bases de datos y sus mediciones desde el servidor remoto al servidor local.

        :return: None
        """
        if self.databases_and_measurements_to_copy is None:
            self.logger.error(
                "No se han especificado bases de datos y mediciones para copiar."
            )
            return

        # Itera sobre las bases de datos y sus mediciones a copiar
        for database, measurements in self.databases_and_measurements_to_copy.items():
            # Cambia a las bases de datos correspondientes en origen y destino
            if self.databases_and_measurements_to_copy is None:
                self.logger.error(
                    "No se han especificado bases de datos y mediciones para copiar."
                )
                return

            if not self.source_client or not self.destination_client:
                self.logger.error("Clientes de InfluxDB no inicializados.")
                return

            self.logger.info(f"Copiando registros de la base de datos '{database}'...")

            # Copia cada medicion dentro de la base de datos actual
            for measurement in measurements:
                self.logger.info(f"\tCopiando tabla '{measurement}'...")
                selectors = self.get_selectors_to_do_average(measurement)
                querys = self.build_queries(selectors, measurement)
                self.read_and_write_data(querys, measurement)

    def run(self) -> None:
        """Metodo principal para ejecutar el flujo completo."""
        self.logger.info("Inicializando el proceso de copia de datos...")

        try:
            self.setup_clients()
            self.get_measurements_to_copy()
            self.copy_databases()
        except Exception:
            txt_error = "Error al ejecutar el proceso de copia de datos."
            self.error.throw_error(txt_error, self.logger)

        self.logger.info("Proceso finalizado de copia de datos.\n")


if __name__ == "__main__":
    backup = BackupInfluxdb()
    backup.run()
