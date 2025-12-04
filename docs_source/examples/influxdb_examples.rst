===========================
Ejemplos de InfluxDB
===========================

Validación de Datos
===================

Validar DataFrame antes de escribir::

   import pandas as pd
   import numpy as np
   from ctrutils import InfluxdbOperation

   # DataFrame con datos problemáticos
   df = pd.DataFrame({
       'value': [1.0, np.nan, np.inf, 3.0],
       'sensor': ['A', 'B', 'C', 'D']
   })

   influx = InfluxdbOperation(host='localhost', port=8086)

   # Escribir con limpieza automática
   stats = influx.write_dataframe(
       measurement='mediciones',
       data=df,
       database='mi_db',
       validate_data=True,  # Limpia NaN/inf automáticamente
       action_on_invalid='remove'
   )

   print(f"Puntos válidos escritos: {stats['successful_points']}")
   print(f"Puntos inválidos eliminados: {stats.get('invalid_points_removed', 0)}")

Escritura Paralela
==================

Para DataFrames grandes (>10k filas)::

   import pandas as pd
   from ctrutils import InfluxdbOperation

   # DataFrame grande
   df = pd.DataFrame({
       'value': range(100000),
       'sensor': ['A'] * 100000
   })

   influx = InfluxdbOperation(host='localhost', port=8086)

   # Escritura paralela con callback
   def progress_callback(batch_num, total_batches):
       print(f"Procesando batch {batch_num}/{total_batches}")

   stats = influx.write_dataframe_parallel(
       measurement='datos_masivos',
       data=df,
       database='mi_db',
       batch_size=5000,
       max_workers=4,
       progress_callback=progress_callback
   )

   print(f"Total puntos escritos: {stats['total_points']}")
   print(f"Tiempo total: {stats['total_time']:.2f}s")

Backup y Restore
================

Exportar y restaurar datos::

   from ctrutils import InfluxdbOperation

   influx = InfluxdbOperation(host='localhost', port=8086)

   # Backup a CSV
   backup_file = influx.backup_measurement(
       database='mi_db',
       measurement='mediciones',
       output_file='backup_mediciones.csv',
       start_time='2024-01-01T00:00:00Z',
       end_time='2024-12-31T23:59:59Z'
   )

   print(f"Backup guardado en: {backup_file}")

   # Restore desde CSV
   stats = influx.restore_measurement(
       database='mi_db',
       measurement='mediciones_restored',
       csv_file='backup_mediciones.csv',
       batch_size=1000
   )

   print(f"Restaurados: {stats['successful_points']} puntos")

Consultas Avanzadas
====================

Usar query builder para consultas complejas::

   from ctrutils import InfluxdbOperation

   influx = InfluxdbOperation(host='localhost', port=8086)

   # Construir query dinámica
   query = influx.query_builder(
       measurement='sensores',
       fields=['temperatura', 'humedad'],
       start_time='2024-01-01T00:00:00Z',
       end_time='2024-01-31T23:59:59Z',
       where_conditions={'location': 'sala1'},
       limit=1000
   )

   result = influx.execute_query_builder(query, return_dataframe=True)
   print(result.describe())

Ver Código Completo
===================

El código completo de estos ejemplos está disponible en el repositorio GitHub.

Referencia de API
=================

Para documentación completa de todos los métodos, consulta :doc:`../api/influxdb`.
