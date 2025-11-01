"""
Este modulo proporciona la clase `InfluxdbOperation` para manejar operaciones en una base de datos
InfluxDB utilizando un cliente `InfluxDBClient`.
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timezone
import math
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager

import pandas as pd  # type: ignore
import numpy as np  # type: ignore
from influxdb import InfluxDBClient


class InfluxdbOperation:
    """
    Clase para manejar la conexion y operaciones en una base de datos InfluxDB.

    Esta clase proporciona una interfaz completa para interactuar con InfluxDB,
    incluyendo validacion avanzada de datos, limpieza de NaN, escritura por lotes
    de DataFrames grandes, y operaciones de administracion de base de datos.

    Ejemplos:
        >>> # Crear instancia con credenciales
        >>> influx = InfluxdbOperation(
        ...     host='localhost',
        ...     port=8086,
        ...     username='admin',
        ...     password='password'
        ... )

        >>> # O usar un cliente existente
        >>> client = InfluxDBClient(host='localhost', port=8086)
        >>> influx = InfluxdbOperation(client=client)

        >>> # Escribir un DataFrame grande con validacion
        >>> df = pd.DataFrame(...)
        >>> influx.write_dataframe(
        ...     measurement='mi_medicion',
        ...     data=df,
        ...     database='mi_db',
        ...     batch_size=1000,
        ...     validate_data=True
        ... )
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[Union[int, str]] = None,
        timeout: Optional[Union[int, float]] = 5,
        client: Optional[InfluxDBClient] = None,
        **kwargs: Any,
    ):
        """
        Inicializa la conexion y la clase `InfluxdbOperation`.

        Args:
            host: Direccion del servidor InfluxDB (requerido si client no se proporciona).
            port: Puerto del servidor InfluxDB (requerido si client no se proporciona).
            timeout: Tiempo de espera para las operaciones en segundos.
            client: Cliente InfluxDBClient existente (opcional). Si se proporciona,
                   se usara este cliente en lugar de crear uno nuevo.
            **kwargs: Argumentos adicionales para InfluxDBClient (username, password, etc.).

        Raises:
            ValueError: Si no se proporciona ni cliente ni host/port.
        """
        if client is not None:
            # Usar el cliente proporcionado
            self._client = client
            self._is_external_client = True
            # Intentar extraer informacion del cliente
            self.host = getattr(client, '_host', None)
            self.port = getattr(client, '_port', None)
            self.timeout = getattr(client, '_timeout', timeout)
        elif host is not None and port is not None:
            # Crear un nuevo cliente
            self.host = host
            self.port = port
            self.timeout = timeout
            self._is_external_client = False
            self._headers = {"Accept": "application/json"}
            self._gzip = True

            self._client = InfluxDBClient(
                host=host,
                port=port,
                timeout=timeout,
                headers=self._headers,
                gzip=self._gzip,
                **kwargs,
            )
        else:
            raise ValueError(
                "Debe proporcionar un cliente existente (client) o "
                "las credenciales de conexion (host y port)."
            )

        self._database: Optional[str] = None
        self._headers = {"Accept": "application/json"}
        self._gzip = True
        self._logger: Optional[logging.Logger] = None
        self._retry_attempts = 3
        self._retry_delay = 1  # segundos
        self._metrics = {
            'total_writes': 0,
            'total_points': 0,
            'failed_writes': 0,
            'total_write_time': 0.0
        }

    # ==================== UTILIDADES INTERNAS ====================

    @staticmethod
    def _convert_to_utc_iso(dt: Union[str, datetime, pd.Timestamp]) -> str:
        """
        Convierte un datetime a formato ISO8601 en UTC.

        Args:
            dt: Datetime a convertir (string, datetime o Timestamp).

        Returns:
            String en formato ISO8601 UTC.
        """
        if isinstance(dt, str):
            # Ya es string, asumimos que está en formato correcto
            return dt
        elif isinstance(dt, pd.Timestamp):
            dt = dt.to_pydatetime()

        # Convertir a UTC si tiene timezone, o asumirlo como UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        return dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    def _setup_logger(
        self,
        name: str = 'InfluxdbOperation',
        level: int = logging.INFO,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Configura el logger para la clase.

        Args:
            name: Nombre del logger.
            level: Nivel de logging.
            logger: Logger personalizado (opcional). Si se proporciona, se usa en lugar de crear uno nuevo.
        """
        if logger:
            self._logger = logger
        else:
            self._logger = logging.getLogger(name)
            self._logger.setLevel(level)
            if not self._logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self._logger.addHandler(handler)

    def enable_logging(
        self,
        level: int = logging.INFO,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Activa el logging para debugging y monitoreo.

        Args:
            level: Nivel de logging (logging.DEBUG, INFO, WARNING, ERROR).
            logger: Instancia de logger personalizado (opcional). Si se proporciona,
                    se usa en lugar de crear uno nuevo.

        Ejemplos:
            >>> # Con logging estándar
            >>> influx = InfluxdbOperation(host='localhost', port=8086)
            >>> influx.enable_logging(logging.DEBUG)

            >>> # Con LoggingHandler de ctrutils
            >>> from ctrutils.handler import LoggingHandler
            >>> handler = LoggingHandler()
            >>> custom_logger = handler.add_handlers([
            ...     handler.create_stream_handler(),
            ...     handler.create_file_handler('influxdb.log')
            ... ])
            >>> influx.enable_logging(logger=custom_logger)
        """
        self._setup_logger(level=level, logger=logger)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Obtiene métricas de rendimiento de las operaciones.

        Returns:
            Diccionario con métricas de escritura.

        Ejemplos:
            >>> metrics = influx.get_metrics()
            >>> print(f"Total writes: {metrics['total_writes']}")
            >>> print(f"Avg write time: {metrics['avg_write_time']:.2f}s")
        """
        avg_time = (
            self._metrics['total_write_time'] / self._metrics['total_writes']
            if self._metrics['total_writes'] > 0 else 0
        )
        return {
            **self._metrics,
            'avg_write_time': avg_time,
            'success_rate': (
                (self._metrics['total_writes'] - self._metrics['failed_writes']) /
                self._metrics['total_writes'] * 100
                if self._metrics['total_writes'] > 0 else 0
            )
        }

    def reset_metrics(self) -> None:
        """Reinicia las métricas de rendimiento."""
        self._metrics = {
            'total_writes': 0,
            'total_points': 0,
            'failed_writes': 0,
            'total_write_time': 0.0
        }

    def _retry_operation(
        self,
        operation: Callable,
        *args,
        max_attempts: Optional[int] = None,
        **kwargs
    ) -> Any:
        """
        Ejecuta una operación con reintentos automáticos.

        Args:
            operation: Función a ejecutar.
            max_attempts: Número máximo de intentos (usa self._retry_attempts si es None).
            *args, **kwargs: Argumentos para la operación.

        Returns:
            Resultado de la operación.

        Raises:
            Exception: Si todos los intentos fallan.
        """
        attempts = max_attempts or self._retry_attempts
        last_exception = None

        for attempt in range(attempts):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if self._logger:
                    self._logger.warning(
                        f"Intento {attempt + 1}/{attempts} falló: {e}"
                    )
                if attempt < attempts - 1:
                    # Backoff exponencial
                    sleep_time = self._retry_delay * (2 ** attempt)
                    time.sleep(sleep_time)

        raise last_exception or Exception("Operación falló después de reintentos")

    @contextmanager
    def transaction(self, database: Optional[str] = None):
        """
        Context manager para operaciones transaccionales.

        Args:
            database: Base de datos para la transacción.

        Ejemplos:
            >>> with influx.transaction('mi_db') as db:
            ...     influx.write_dataframe(measurement='datos', data=df)
            ...     influx.write_points(points=points)
        """
        if database:
            original_db = self._database
            self.switch_database(database)

        try:
            yield self
        except Exception as e:
            if self._logger:
                self._logger.error(f"Error en transacción: {e}")
            raise
        finally:
            if database and original_db:
                self.switch_database(original_db)

    @property
    def get_client_info(self) -> Dict[str, Any]:
        """
        Obtiene informacion del cliente actual.
        """
        return {
            "host": self.host,
            "port": self.port,
            "database": self._database,
            "timeout": self.timeout,
            "headers": self._headers,
            "gzip": self._gzip,
        }

    @property
    def get_client(self) -> InfluxDBClient:
        """
        Obtiene el cliente actual `InfluxDBClient`.
        """
        return self._client

    def close_client(self) -> None:
        """
        Cierra la conexion actual del cliente `InfluxDBClient`.

        Nota: Si el cliente fue proporcionado externamente, no se cerrara automaticamente
        para evitar efectos secundarios en otros componentes que lo usen.
        """
        if not self._is_external_client:
            self._client.close()

    def switch_database(self, database: str) -> None:
        """
        Cambia la base de datos activa en el cliente de InfluxDB.
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
            df.index = pd.to_datetime(df.index)

        return df

    def normalize_value_to_write(self, value: Any) -> Any:
        """
        Normaliza el valor para su escritura en InfluxDB.

        Esta funcion valida y convierte valores para asegurar compatibilidad con InfluxDB.

        Args:
            value: Valor a normalizar.

        Returns:
            Valor normalizado o None si no es valido.
        """
        # Verificar si es NaN, None o infinito
        if value is None:
            return None

        # Manejar valores numericos especiales
        if isinstance(value, (int, float, np.integer, np.floating)):
            # Convertir tipos numpy a tipos nativos Python
            if isinstance(value, (np.integer, np.int64, np.int32, np.int16, np.int8)):
                value = int(value)
            elif isinstance(value, (np.floating, np.float64, np.float32, np.float16)):
                value = float(value)

            # Verificar NaN e infinitos
            if isinstance(value, float):
                if math.isnan(value) or math.isinf(value):
                    return None
                return value
            elif isinstance(value, int):
                return float(value)

        # Manejar booleanos
        elif isinstance(value, (bool, np.bool_)):
            return bool(value)

        # Manejar strings
        elif isinstance(value, (str, np.str_)):
            value_str = str(value).strip()
            # Filtrar strings vacios o con valores especiales
            if value_str in ['', 'nan', 'NaN', 'None', 'null', 'NULL']:
                return None
            return value_str

        # Manejar pandas.NA o numpy.nan
        elif pd.isna(value):
            return None

        return value

    def _validate_point(self, point: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Valida y limpia un punto antes de escribirlo en InfluxDB.

        Args:
            point: Diccionario representando un punto de datos.

        Returns:
            Punto validado o None si no es valido.
        """
        if not point or 'fields' not in point:
            return None

        # Filtrar campos con valores None o NaN
        validated_fields = {}
        for field_key, field_value in point['fields'].items():
            normalized_value = self.normalize_value_to_write(field_value)
            if normalized_value is not None:
                validated_fields[field_key] = normalized_value

        # Si no quedan campos validos, el punto es invalido
        if not validated_fields:
            return None

        point['fields'] = validated_fields
        return point

    def write_points(
        self,
        points: list,
        database: Optional[str] = None,
        tags: Optional[dict] = None,
        batch_size: int = 5000,
        validate_data: bool = True,
    ) -> Dict[str, int]:
        """
        Escribe una lista de puntos directamente en InfluxDB, asegurando que el timestamp este en UTC.

        Args:
            points: Lista de puntos a escribir. Cada punto debe ser un diccionario con
                   las claves 'measurement', 'time', 'fields' y opcionalmente 'tags'.
            database: Nombre de la base de datos donde escribir (opcional si ya esta configurada).
            tags: Tags adicionales para agregar a todos los puntos.
            batch_size: Tamaño del lote para escritura. Por defecto 5000.
            validate_data: Si True, valida y limpia los puntos antes de escribir.

        Returns:
            Diccionario con estadisticas de escritura: {
                'total_points': int,
                'written_points': int,
                'invalid_points': int,
                'batches': int
            }

        Raises:
            ValueError: Si no se proporciona base de datos o la lista de puntos esta vacia.
        """
        db_to_use = database or self._database
        if db_to_use is None:
            raise ValueError(
                "Debe proporcionar una base de datos o establecerla mediante el metodo 'switch_database'."
            )
        self.switch_database(db_to_use)

        if not points:
            raise ValueError("La lista de puntos no puede estar vacia.")

        total_points = len(points)
        validated_points = []
        invalid_count = 0

        for point in points:
            # Convertir timestamp a UTC
            if "time" in point:
                point["time"] = self._convert_to_utc_iso(point["time"])

            # Agregar tags adicionales
            if tags:
                point["tags"] = {**point.get("tags", {}), **tags}

            # Validar el punto si se solicita
            if validate_data:
                validated_point = self._validate_point(point)
                if validated_point is not None:
                    validated_points.append(validated_point)
                else:
                    invalid_count += 1
            else:
                validated_points.append(point)

        # Escribir en lotes
        written_count = 0
        batch_count = 0
        for i in range(0, len(validated_points), batch_size):
            batch = validated_points[i:i + batch_size]
            self._client.write_points(
                points=batch, database=db_to_use, batch_size=batch_size
            )
            written_count += len(batch)
            batch_count += 1

        return {
            'total_points': total_points,
            'written_points': written_count,
            'invalid_points': invalid_count,
            'batches': batch_count
        }

    def write_dataframe(
        self,
        measurement: str,
        data: pd.DataFrame,
        tags: Optional[dict] = None,
        database: Optional[str] = None,
        batch_size: int = 1000,
        validate_data: bool = True,
        pass_to_float: bool = True,
        convert_bool_to_float: bool = False,
        suffix_bool_to_float: str = "_bool_to_float",
        drop_na_rows: bool = False,
    ) -> Dict[str, int]:
        """
        Convierte un DataFrame en una lista de puntos y los escribe en InfluxDB,
        con validacion avanzada y limpieza de datos.

        Este metodo maneja automaticamente:
        - Valores NaN, None, e infinitos
        - Conversion de tipos numpy a tipos nativos Python
        - Validacion de cada punto antes de escribir
        - Escritura por lotes para DataFrames grandes
        - Conversion de timestamps a UTC

        Args:
            measurement: Nombre de la medicion en InfluxDB.
            data: DataFrame con los datos a escribir. El indice debe ser DatetimeIndex.
            tags: Tags adicionales para todos los puntos (opcional).
            database: Base de datos donde escribir (opcional si ya esta configurada).
            batch_size: Tamaño del lote para escritura. Por defecto 1000.
                       Reducir si tiene problemas de memoria con DataFrames grandes.
            validate_data: Si True, valida y limpia datos antes de escribir.
            pass_to_float: Si True, convierte enteros a float para compatibilidad InfluxDB.
            convert_bool_to_float: Si True, convierte columnas booleanas a float.
            suffix_bool_to_float: Sufijo para columnas booleanas convertidas.
            drop_na_rows: Si True, elimina filas donde todos los valores son NaN.

        Returns:
            Diccionario con estadisticas de escritura.

        Raises:
            ValueError: Si no se proporciona DataFrame o measurement.
            TypeError: Si el indice del DataFrame no es DatetimeIndex.

        Ejemplos:
            >>> df = pd.DataFrame({
            ...     'temperatura': [20.5, np.nan, 21.0, 22.5],
            ...     'humedad': [45.0, 50.0, np.nan, 55.0]
            ... }, index=pd.date_range('2024-01-01', periods=4, freq='H'))
            >>>
            >>> stats = influx.write_dataframe(
            ...     measurement='clima',
            ...     data=df,
            ...     database='mi_db',
            ...     batch_size=1000,
            ...     validate_data=True
            ... )
            >>> print(f"Escritos: {stats['written_points']}/{stats['total_points']}")
        """
        if data is None or measurement is None:
            raise ValueError(
                "Debe proporcionar un DataFrame 'data' y un 'measurement'."
            )

        if not isinstance(data.index, pd.DatetimeIndex):
            raise TypeError("El indice del DataFrame debe ser de tipo DatetimeIndex.")

        # Crear una copia para no modificar el original
        df = data.copy()

        # Eliminar filas completamente vacias si se solicita
        if drop_na_rows:
            df = df.dropna(how='all')

        # Convertir columnas booleanas si se solicita
        if convert_bool_to_float:
            for column in df.select_dtypes(include=["bool"]).columns:
                df[f"{column}{suffix_bool_to_float}"] = df[column].astype(float)
                df = df.drop(columns=[column])

        # Convertir DataFrame a lista de diccionarios de puntos
        points = []
        for index, row in df.iterrows():
            # Construir los campos, aplicando normalizacion
            fields = {}
            for field, value in row.items():
                # Saltar valores NaN
                if pd.isna(value):
                    continue

                # Normalizar el valor
                if validate_data:
                    normalized_value = self.normalize_value_to_write(value)
                    if normalized_value is not None:
                        fields[field] = normalized_value
                else:
                    # Sin validacion, solo aplicar conversion basica
                    if pass_to_float and isinstance(value, (int, np.integer)):
                        fields[field] = float(value)
                    else:
                        fields[field] = value

            # Solo agregar el punto si tiene campos validos
            if fields:
                point = {
                    "measurement": measurement,
                    "time": self._convert_to_utc_iso(index),
                    "fields": fields,
                }

                # Agregar tags si se proporcionaron
                if tags:
                    point["tags"] = tags

                points.append(point)

        # Escribir los puntos usando el metodo write_points mejorado
        return self.write_points(
            points=points,
            database=database,
            tags=None,  # Ya los agregamos arriba
            batch_size=batch_size,
            validate_data=False,  # Ya validamos arriba
        )

    def write_dataframe_parallel(
        self,
        df: pd.DataFrame,
        measurement: str,
        tags: Optional[Dict[str, str]] = None,
        field_columns: Optional[List[str]] = None,
        tag_columns: Optional[List[str]] = None,
        batch_size: int = 5000,
        max_workers: int = 4,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        database: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Escribe un DataFrame a InfluxDB usando procesamiento paralelo.

        Args:
            df: DataFrame con datos a escribir
            measurement: Nombre de la medicion
            tags: Tags adicionales a agregar a todos los puntos
            field_columns: Columnas a usar como fields (None = todas las numericas)
            tag_columns: Columnas a usar como tags
            batch_size: Tamaño de cada batch
            max_workers: Numero maximo de threads para procesamiento paralelo
            progress_callback: Funcion opcional(processed, total) para reportar progreso
            database: Nombre de la base de datos (None = usa la actual)

        Returns:
            Diccionario con estadisticas de la operacion
        """
        if df.empty:
            return {"total_points": 0, "successful": 0, "failed": 0, "duration": 0.0}

        start_time = time.time()
        total_rows = len(df)
        processed = 0
        successful = 0
        failed = 0

        # Dividir DataFrame en chunks
        chunks = [df.iloc[i:i + batch_size] for i in range(0, total_rows, batch_size)]

        # Funcion para procesar cada chunk
        def process_chunk(chunk_data):
            try:
                stats = self.write_dataframe(
                    df=chunk_data,
                    measurement=measurement,
                    tags=tags,
                    field_columns=field_columns,
                    tag_columns=tag_columns,
                    batch_size=batch_size,
                    validate_data=True,
                    database=database
                )
                return stats['successful'], stats['failed']
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Error procesando chunk: {e}")
                return 0, len(chunk_data)

        # Procesar chunks en paralelo
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_chunk, chunk): i
                      for i, chunk in enumerate(chunks)}

            for future in futures:
                chunk_success, chunk_failed = future.result()
                successful += chunk_success
                failed += chunk_failed
                processed += chunk_success + chunk_failed

                if progress_callback:
                    progress_callback(processed, total_rows)

        duration = time.time() - start_time

        result = {
            "total_points": total_rows,
            "successful": successful,
            "failed": failed,
            "duration": duration,
            "points_per_second": successful / duration if duration > 0 else 0
        }

        if self._logger:
            self._logger.info(f"Escritura paralela completada: {result}")

        return result

    def downsample_data(
        self,
        measurement: str,
        target_measurement: str,
        aggregation_window: str,
        aggregation_func: str = "MEAN",
        fields: Optional[List[str]] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        database: Optional[str] = None,
    ) -> int:
        """
        Crea una version downsampled de los datos.

        Args:
            measurement: Measurement de origen
            target_measurement: Measurement de destino
            aggregation_window: Ventana de agregacion (ej: '1h', '1d')
            aggregation_func: Funcion de agregacion (MEAN, SUM, MAX, MIN, COUNT)
            fields: Campos a agregar (None = todos)
            start_time: Tiempo de inicio (formato RFC3339)
            end_time: Tiempo de fin (formato RFC3339)
            database: Base de datos (None = usa la actual)

        Returns:
            Numero de puntos creados
        """
        db_to_use = database or self._database
        if db_to_use is None:
            raise ValueError("Debe proporcionar una base de datos")

        self.switch_database(db_to_use)

        # Construir query
        field_list = ", ".join([f"{aggregation_func}({f}) AS {f}" for f in fields]) if fields else f"{aggregation_func}(*)"

        query = f"""
            SELECT {field_list}
            INTO "{target_measurement}"
            FROM "{measurement}"
        """

        where_clauses = []
        if start_time:
            where_clauses.append(f"time >= '{start_time}'")
        if end_time:
            where_clauses.append(f"time <= '{end_time}'")

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += f" GROUP BY time({aggregation_window}), *"

        result = self._client.query(query)

        # Contar puntos creados
        count_query = f'SELECT COUNT(*) FROM "{target_measurement}"'
        count_result = self._client.query(count_query)
        points_created = list(count_result.get_points())[0]['count'] if count_result else 0

        if self._logger:
            self._logger.info(f"Downsampling completado: {points_created} puntos creados")

        return points_created

    def create_continuous_query(
        self,
        cq_name: str,
        measurement: str,
        target_measurement: str,
        aggregation_window: str,
        aggregation_func: str = "MEAN",
        fields: Optional[List[str]] = None,
        database: Optional[str] = None,
    ) -> None:
        """
        Crea una continuous query para downsampling automatico.

        Args:
            cq_name: Nombre de la continuous query
            measurement: Measurement de origen
            target_measurement: Measurement de destino
            aggregation_window: Ventana de agregacion
            aggregation_func: Funcion de agregacion
            fields: Campos a agregar
            database: Base de datos
        """
        db_to_use = database or self._database
        if db_to_use is None:
            raise ValueError("Debe proporcionar una base de datos")

        field_list = ", ".join([f"{aggregation_func}({f}) AS {f}" for f in fields]) if fields else f"{aggregation_func}(*)"

        query = f"""
            CREATE CONTINUOUS QUERY "{cq_name}" ON "{db_to_use}"
            BEGIN
                SELECT {field_list}
                INTO "{target_measurement}"
                FROM "{measurement}"
                GROUP BY time({aggregation_window}), *
            END
        """

        self._client.query(query)

        if self._logger:
            self._logger.info(f"Continuous query '{cq_name}' creada exitosamente")

    def list_continuous_queries(self, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista todas las continuous queries.

        Returns:
            Lista de diccionarios con informacion de las CQs
        """
        db_to_use = database or self._database
        result = self._client.query("SHOW CONTINUOUS QUERIES")

        cqs = []
        for point in result.get_points():
            if not db_to_use or point.get('database') == db_to_use:
                cqs.append(dict(point))

        return cqs

    def drop_continuous_query(self, cq_name: str, database: Optional[str] = None) -> None:
        """
        Elimina una continuous query.

        Args:
            cq_name: Nombre de la CQ a eliminar
            database: Base de datos
        """
        db_to_use = database or self._database
        if db_to_use is None:
            raise ValueError("Debe proporcionar una base de datos")

        query = f'DROP CONTINUOUS QUERY "{cq_name}" ON "{db_to_use}"'
        self._client.query(query)

        if self._logger:
            self._logger.info(f"Continuous query '{cq_name}' eliminada")

    def backup_measurement(
        self,
        measurement: str,
        output_file: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        database: Optional[str] = None,
    ) -> int:
        """
        Exporta un measurement a archivo CSV.

        Args:
            measurement: Nombre del measurement
            output_file: Ruta del archivo CSV de salida
            start_time: Tiempo de inicio (opcional)
            end_time: Tiempo de fin (opcional)
            database: Base de datos (None = usa la actual)

        Returns:
            Numero de puntos exportados
        """
        df = self.query_to_dataframe(
            measurement=measurement,
            start_time=start_time,
            end_time=end_time,
            database=database
        )

        if df.empty:
            if self._logger:
                self._logger.warning(f"No hay datos para exportar del measurement '{measurement}'")
            return 0

        df.to_csv(output_file, index=True)

        if self._logger:
            self._logger.info(f"Backup completado: {len(df)} puntos exportados a '{output_file}'")

        return len(df)

    def restore_measurement(
        self,
        measurement: str,
        input_file: str,
        tags: Optional[Dict[str, str]] = None,
        batch_size: int = 5000,
        database: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Restaura un measurement desde archivo CSV.

        Args:
            measurement: Nombre del measurement de destino
            input_file: Ruta del archivo CSV
            tags: Tags adicionales
            batch_size: Tamaño de batch para escritura
            database: Base de datos de destino

        Returns:
            Estadisticas de la operacion
        """
        df = pd.read_csv(input_file, index_col=0, parse_dates=True)

        if df.empty:
            return {"total_points": 0, "successful": 0, "failed": 0}

        result = self.write_dataframe(
            df=df,
            measurement=measurement,
            tags=tags,
            batch_size=batch_size,
            database=database
        )

        if self._logger:
            self._logger.info(f"Restauracion completada: {result}")

        return result

    def calculate_data_quality_metrics(
        self,
        measurement: str,
        fields: Optional[List[str]] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        database: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calcula metricas de calidad de datos para un measurement.

        Args:
            measurement: Nombre del measurement
            fields: Campos a analizar (None = todos)
            start_time: Tiempo de inicio
            end_time: Tiempo de fin
            database: Base de datos

        Returns:
            Diccionario con metricas por campo
        """
        df = self.query_to_dataframe(
            measurement=measurement,
            fields=fields,
            start_time=start_time,
            end_time=end_time,
            database=database
        )

        if df.empty:
            return {}

        metrics = {}
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                metrics[col] = {
                    "count": int(df[col].count()),
                    "missing": int(df[col].isna().sum()),
                    "missing_percentage": float(df[col].isna().sum() / len(df) * 100),
                    "mean": float(df[col].mean()) if df[col].count() > 0 else None,
                    "std": float(df[col].std()) if df[col].count() > 1 else None,
                    "min": float(df[col].min()) if df[col].count() > 0 else None,
                    "max": float(df[col].max()) if df[col].count() > 0 else None,
                    "zeros": int((df[col] == 0).sum()),
                    "outliers": int(self._count_outliers(df[col])),
                }
            else:
                metrics[col] = {
                    "count": int(df[col].count()),
                    "missing": int(df[col].isna().sum()),
                    "missing_percentage": float(df[col].isna().sum() / len(df) * 100),
                    "unique_values": int(df[col].nunique()),
                }

        return metrics

    @staticmethod
    def _count_outliers(series: pd.Series, threshold: float = 3.0) -> int:
        """
        Cuenta outliers usando el metodo de desviacion estandar.

        Args:
            series: Serie de pandas
            threshold: Numero de desviaciones estandar para considerar outlier

        Returns:
            Numero de outliers
        """
        if series.count() < 2:
            return 0

        mean = series.mean()
        std = series.std()

        if std == 0:
            return 0

        z_scores = np.abs((series - mean) / std)
        return int((z_scores > threshold).sum())

    def query_builder(
        self,
        measurement: str,
        fields: Optional[List[str]] = None,
        where_conditions: Optional[Dict[str, Any]] = None,
        group_by: Optional[List[str]] = None,
        order_by: str = "time DESC",
        limit: Optional[int] = None,
        database: Optional[str] = None,
    ) -> str:
        """
        Constructor de queries InfluxQL avanzado.

        Args:
            measurement: Nombre del measurement
            fields: Campos a seleccionar (None = todos)
            where_conditions: Condiciones WHERE como diccionario
            group_by: Campos para agrupar
            order_by: Orden de resultados
            limit: Limite de resultados
            database: Base de datos

        Returns:
            Query InfluxQL como string
        """
        # SELECT
        field_str = ", ".join(fields) if fields else "*"
        query = f'SELECT {field_str} FROM "{measurement}"'

        # WHERE
        if where_conditions:
            where_clauses = []
            for key, value in where_conditions.items():
                if isinstance(value, str):
                    where_clauses.append(f'"{key}" = \'{value}\'')
                elif isinstance(value, (list, tuple)):
                    # Para operadores como IN, >, <, etc
                    operator, val = value
                    if isinstance(val, str):
                        where_clauses.append(f'"{key}" {operator} \'{val}\'')
                    else:
                        where_clauses.append(f'"{key}" {operator} {val}')
                else:
                    where_clauses.append(f'"{key}" = {value}')

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

        # GROUP BY
        if group_by:
            query += " GROUP BY " + ", ".join(group_by)

        # ORDER BY
        if order_by:
            query += f" ORDER BY {order_by}"

        # LIMIT
        if limit:
            query += f" LIMIT {limit}"

        return query

    def execute_query_builder(
        self,
        measurement: str,
        fields: Optional[List[str]] = None,
        where_conditions: Optional[Dict[str, Any]] = None,
        group_by: Optional[List[str]] = None,
        order_by: str = "time DESC",
        limit: Optional[int] = None,
        as_dataframe: bool = True,
        database: Optional[str] = None,
    ) -> Union[pd.DataFrame, Any]:
        """
        Construye y ejecuta una query.

        Args:
            measurement: Nombre del measurement
            fields: Campos a seleccionar
            where_conditions: Condiciones WHERE
            group_by: Campos para agrupar
            order_by: Orden de resultados
            limit: Limite de resultados
            as_dataframe: Si retornar como DataFrame
            database: Base de datos

        Returns:
            DataFrame o resultado de query
        """
        query = self.query_builder(
            measurement=measurement,
            fields=fields,
            where_conditions=where_conditions,
            group_by=group_by,
            order_by=order_by,
            limit=limit,
            database=database
        )

        if as_dataframe:
            db_to_use = database or self._database
            if db_to_use:
                self.switch_database(db_to_use)

            result = self._client.query(query)
            if result:
                df = pd.DataFrame(list(result.get_points()))
                if not df.empty and 'time' in df.columns:
                    df['time'] = pd.to_datetime(df['time'])
                    df.set_index('time', inplace=True)
                return df
            return pd.DataFrame()
        else:
            return self._client.query(query)

    def delete(
        self,
        measurement: str,
        start_time: Optional[Union[str, pd.Timestamp]] = None,
        end_time: Optional[Union[str, pd.Timestamp]] = None,
        filters: Optional[Dict[str, str]] = None,
        database: Optional[str] = None,
    ) -> None:
        """
        Elimina datos de una medicion en InfluxDB.
        """
        db_to_use = database or self._database
        if db_to_use is None:
            raise ValueError(
                "Debe proporcionar una base de datos o establecerla mediante el metodo 'switch_database'."
            )
        self.switch_database(db_to_use)

        query = f"DELETE FROM \"{measurement}\""
        where_clauses = []

        if start_time:
            start_time_utc = self._convert_to_utc_iso(start_time)
            where_clauses.append(f"time >= '{start_time_utc}'")

        if end_time:
            end_time_utc = self._convert_to_utc_iso(end_time)
            where_clauses.append(f"time <= '{end_time_utc}'")

        if filters:
            for key, value in filters.items():
                where_clauses.append(f"\"{key}\" = '{value}'")

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        self._client.query(query)

    def get_field_keys_grouped_by_type(self, measurement: str) -> Dict[str, List[str]]:
        """
        Obtiene las claves de un measurement, agrupadas por tipo de dato.
        """
        query = f"SHOW FIELD KEYS FROM \"{measurement}\""
        results = list(self._client.query(query).get_points())
        field_type_dict = defaultdict(list)

        for result in results:
            field_type_dict[result["fieldType"]].append(result["fieldKey"])

        return dict(field_type_dict)

    def build_query_fields(
        self, fields: Union[List[str], Dict[str, List[str]]], operation: str
    ) -> Dict[str, str]:
        """
        Construye una parte de la consulta de InfluxDB aplicando una operacion a cada campo.
        """
        query_fields = defaultdict(str)

        if isinstance(fields, list):
            query_fields["fields"] = ", ".join(
                [f'{operation}("{field}") AS "{field}"' for field in fields]
            )

        if isinstance(fields, dict):
            for field_type, field_list in fields.items():
                if field_type in ["boolean", "integer"]:
                    query_parts = [f'"{field}"' for field in field_list]
                else:
                    query_parts = [
                        f'{operation}("{field}") AS "{field}"'
                        for field in field_list
                    ]
                query_fields[field_type] = ", ".join(query_parts)

        return dict(query_fields)

    # ==================== METODOS ADMINISTRATIVOS ====================

    def list_databases(self) -> List[str]:
        """
        Lista todas las bases de datos disponibles en InfluxDB.

        Returns:
            Lista con los nombres de las bases de datos.

        Ejemplos:
            >>> influx = InfluxdbOperation(host='localhost', port=8086)
            >>> databases = influx.list_databases()
            >>> print(databases)
            ['_internal', 'mi_db', 'otra_db']
        """
        result = self._client.get_list_database()
        return [db['name'] for db in result]

    def database_exists(self, database: str) -> bool:
        """
        Verifica si una base de datos existe.

        Args:
            database: Nombre de la base de datos a verificar.

        Returns:
            True si la base de datos existe, False en caso contrario.
        """
        databases = self.list_databases()
        return database in databases

    def create_database(self, database: str) -> None:
        """
        Crea una nueva base de datos en InfluxDB.

        Args:
            database: Nombre de la base de datos a crear.

        Ejemplos:
            >>> influx.create_database('nueva_db')
        """
        self._client.create_database(database)

    def drop_database(self, database: str, confirm: bool = False) -> None:
        """
        Elimina una base de datos de InfluxDB.

        Args:
            database: Nombre de la base de datos a eliminar.
            confirm: Debe ser True para confirmar la eliminacion (seguridad).

        Raises:
            ValueError: Si confirm no es True.

        Ejemplos:
            >>> influx.drop_database('vieja_db', confirm=True)
        """
        if not confirm:
            raise ValueError(
                "Debe confirmar la eliminacion de la base de datos estableciendo confirm=True"
            )
        self._client.drop_database(database)

    def list_measurements(self, database: Optional[str] = None) -> List[str]:
        """
        Lista todas las mediciones en una base de datos.

        Args:
            database: Nombre de la base de datos (opcional si ya esta configurada).

        Returns:
            Lista con los nombres de las mediciones.

        Ejemplos:
            >>> measurements = influx.list_measurements('mi_db')
            >>> print(measurements)
            ['temperatura', 'humedad', 'presion']
        """
        db_to_use = database or self._database
        if db_to_use is None:
            raise ValueError(
                "Debe proporcionar una base de datos o establecerla mediante el metodo 'switch_database'."
            )
        self.switch_database(db_to_use)

        result = self._client.query("SHOW MEASUREMENTS")
        points = list(result.get_points())
        return [point['name'] for point in points]

    def measurement_exists(self, measurement: str, database: Optional[str] = None) -> bool:
        """
        Verifica si una medicion existe en la base de datos.

        Args:
            measurement: Nombre de la medicion a verificar.
            database: Nombre de la base de datos (opcional si ya esta configurada).

        Returns:
            True si la medicion existe, False en caso contrario.
        """
        measurements = self.list_measurements(database)
        return measurement in measurements

    def drop_measurement(self, measurement: str, database: Optional[str] = None, confirm: bool = False) -> None:
        """
        Elimina una medicion (y todos sus datos) de la base de datos.

        Args:
            measurement: Nombre de la medicion a eliminar.
            database: Nombre de la base de datos (opcional si ya esta configurada).
            confirm: Debe ser True para confirmar la eliminacion (seguridad).

        Raises:
            ValueError: Si confirm no es True.

        Ejemplos:
            >>> influx.drop_measurement('vieja_medicion', confirm=True)
        """
        if not confirm:
            raise ValueError(
                "Debe confirmar la eliminacion de la medicion estableciendo confirm=True"
            )

        db_to_use = database or self._database
        if db_to_use is None:
            raise ValueError(
                "Debe proporcionar una base de datos o establecerla mediante el metodo 'switch_database'."
            )
        self.switch_database(db_to_use)

        self._client.query(f'DROP MEASUREMENT "{measurement}"')

    def list_tags(self, measurement: str, database: Optional[str] = None) -> List[str]:
        """
        Lista todos los tags de una medicion.

        Args:
            measurement: Nombre de la medicion.
            database: Nombre de la base de datos (opcional si ya esta configurada).

        Returns:
            Lista con los nombres de los tags.

        Ejemplos:
            >>> tags = influx.list_tags('temperatura', 'mi_db')
            >>> print(tags)
            ['sensor_id', 'location', 'type']
        """
        db_to_use = database or self._database
        if db_to_use is None:
            raise ValueError(
                "Debe proporcionar una base de datos o establecerla mediante el metodo 'switch_database'."
            )
        self.switch_database(db_to_use)

        query = f'SHOW TAG KEYS FROM "{measurement}"'
        result = self._client.query(query)
        points = list(result.get_points())
        return [point['tagKey'] for point in points]

    def list_tag_values(self, measurement: str, tag_key: str, database: Optional[str] = None) -> List[str]:
        """
        Lista todos los valores de un tag especifico en una medicion.

        Args:
            measurement: Nombre de la medicion.
            tag_key: Nombre del tag.
            database: Nombre de la base de datos (opcional si ya esta configurada).

        Returns:
            Lista con los valores del tag.

        Ejemplos:
            >>> values = influx.list_tag_values('temperatura', 'location', 'mi_db')
            >>> print(values)
            ['salon', 'cocina', 'dormitorio']
        """
        db_to_use = database or self._database
        if db_to_use is None:
            raise ValueError(
                "Debe proporcionar una base de datos o establecerla mediante el metodo 'switch_database'."
            )
        self.switch_database(db_to_use)

        query = f'SHOW TAG VALUES FROM "{measurement}" WITH KEY = "{tag_key}"'
        result = self._client.query(query)
        points = list(result.get_points())
        return [point['value'] for point in points]

    def list_fields(self, measurement: str, database: Optional[str] = None) -> Dict[str, str]:
        """
        Lista todos los campos de una medicion con sus tipos.

        Args:
            measurement: Nombre de la medicion.
            database: Nombre de la base de datos (opcional si ya esta configurada).

        Returns:
            Diccionario con nombres de campos como claves y tipos como valores.

        Ejemplos:
            >>> fields = influx.list_fields('temperatura', 'mi_db')
            >>> print(fields)
            {'temperatura': 'float', 'humedad': 'float', 'activo': 'boolean'}
        """
        db_to_use = database or self._database
        if db_to_use is None:
            raise ValueError(
                "Debe proporcionar una base de datos o establecerla mediante el metodo 'switch_database'."
            )
        self.switch_database(db_to_use)

        query = f'SHOW FIELD KEYS FROM "{measurement}"'
        result = self._client.query(query)
        points = list(result.get_points())
        return {point['fieldKey']: point['fieldType'] for point in points}

    def get_measurement_cardinality(self, measurement: str, database: Optional[str] = None) -> int:
        """
        Obtiene la cardinalidad (numero de series unicas) de una medicion.

        La cardinalidad es el numero de combinaciones unicas de tags en una medicion.
        Una cardinalidad alta puede afectar el rendimiento.

        Args:
            measurement: Nombre de la medicion.
            database: Nombre de la base de datos (opcional si ya esta configurada).

        Returns:
            Numero de series unicas en la medicion.

        Ejemplos:
            >>> cardinality = influx.get_measurement_cardinality('temperatura', 'mi_db')
            >>> print(f"Series unicas: {cardinality}")
        """
        db_to_use = database or self._database
        if db_to_use is None:
            raise ValueError(
                "Debe proporcionar una base de datos o establecerla mediante el metodo 'switch_database'."
            )
        self.switch_database(db_to_use)

        query = f'SHOW SERIES FROM "{measurement}"'
        result = self._client.query(query)
        points = list(result.get_points())
        return len(points)

    def get_retention_policies(self, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista las politicas de retencion de una base de datos.

        Args:
            database: Nombre de la base de datos (opcional si ya esta configurada).

        Returns:
            Lista de diccionarios con informacion de las politicas de retencion.

        Ejemplos:
            >>> policies = influx.get_retention_policies('mi_db')
            >>> for policy in policies:
            ...     print(f"{policy['name']}: {policy['duration']}")
        """
        db_to_use = database or self._database
        if db_to_use is None:
            raise ValueError(
                "Debe proporcionar una base de datos o establecerla mediante el metodo 'switch_database'."
            )
        self.switch_database(db_to_use)

        result = self._client.get_list_retention_policies(db_to_use)
        return result

    def count_points(self, measurement: str, database: Optional[str] = None,
                    start_time: Optional[str] = None, end_time: Optional[str] = None) -> int:
        """
        Cuenta el numero de puntos en una medicion.

        Args:
            measurement: Nombre de la medicion.
            database: Nombre de la base de datos (opcional si ya esta configurada).
            start_time: Tiempo de inicio para el conteo (opcional).
            end_time: Tiempo de fin para el conteo (opcional).

        Returns:
            Numero de puntos en la medicion.

        Ejemplos:
            >>> # Contar todos los puntos
            >>> total = influx.count_points('temperatura', 'mi_db')
            >>> print(f"Total de puntos: {total}")
            >>>
            >>> # Contar puntos en un rango de tiempo
            >>> total = influx.count_points(
            ...     'temperatura',
            ...     'mi_db',
            ...     start_time='2024-01-01T00:00:00Z',
            ...     end_time='2024-01-31T23:59:59Z'
            ... )
        """
        db_to_use = database or self._database
        if db_to_use is None:
            raise ValueError(
                "Debe proporcionar una base de datos o establecerla mediante el metodo 'switch_database'."
            )
        self.switch_database(db_to_use)

        query = f'SELECT COUNT(*) FROM "{measurement}"'

        where_clauses = []
        if start_time:
            where_clauses.append(f"time >= '{start_time}'")
        if end_time:
            where_clauses.append(f"time <= '{end_time}'")

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        result = self._client.query(query)
        points = list(result.get_points())

        if points:
            # Obtener el primer valor de conteo disponible
            for key, value in points[0].items():
                if key.startswith('count_'):
                    return int(value) if value is not None else 0

        return 0

    def get_database_info(self, database: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene informacion completa sobre una base de datos.

        Args:
            database: Nombre de la base de datos (opcional si ya esta configurada).

        Returns:
            Diccionario con informacion de la base de datos:
            - name: Nombre de la base de datos
            - measurements: Lista de mediciones
            - retention_policies: Politicas de retencion

        Ejemplos:
            >>> info = influx.get_database_info('mi_db')
            >>> print(f"Base de datos: {info['name']}")
            >>> print(f"Mediciones: {len(info['measurements'])}")
            >>> for measurement in info['measurements']:
            ...     print(f"  - {measurement}")
        """
        db_to_use = database or self._database
        if db_to_use is None:
            raise ValueError(
                "Debe proporcionar una base de datos o establecerla mediante el metodo 'switch_database'."
            )

        return {
            'name': db_to_use,
            'measurements': self.list_measurements(db_to_use),
            'retention_policies': self.get_retention_policies(db_to_use),
        }

    def get_measurement_info(self, measurement: str, database: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene informacion completa sobre una medicion.

        Args:
            measurement: Nombre de la medicion.
            database: Nombre de la base de datos (opcional si ya esta configurada).

        Returns:
            Diccionario con informacion de la medicion:
            - name: Nombre de la medicion
            - tags: Lista de tags
            - fields: Diccionario de campos con sus tipos
            - cardinality: Numero de series unicas
            - point_count: Numero total de puntos

        Ejemplos:
            >>> info = influx.get_measurement_info('temperatura', 'mi_db')
            >>> print(f"Medicion: {info['name']}")
            >>> print(f"Tags: {info['tags']}")
            >>> print(f"Campos: {info['fields']}")
            >>> print(f"Total puntos: {info['point_count']}")
        """
        db_to_use = database or self._database
        if db_to_use is None:
            raise ValueError(
                "Debe proporcionar una base de datos o establecerla mediante el metodo 'switch_database'."
            )

        return {
            'name': measurement,
            'tags': self.list_tags(measurement, db_to_use),
            'fields': self.list_fields(measurement, db_to_use),
            'cardinality': self.get_measurement_cardinality(measurement, db_to_use),
            'point_count': self.count_points(measurement, db_to_use),
        }

