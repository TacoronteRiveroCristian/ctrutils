# ctrutils# ctrutils



**ctrutils** es una librería minimalista de utilidades en Python enfocada en operaciones con InfluxDB, programación de tareas y logging centralizado.**ctrutils** es una librería minimalista de utilidades en Python enfocada en operaciones con InfluxDB y programación de tareas.



## 📦 Módulos## 📦 Módulos



### 🗄️ InfluxDB Operations### 🗄️ InfluxDB Operations

Operaciones avanzadas con InfluxDB incluyendo:Operaciones avanzadas con InfluxDB incluyendo:

- Validación automática de datos (NaN, infinitos, None)- Validación automática de datos (NaN, infinitos, None)

- Escritura por lotes para DataFrames grandes- Escritura por lotes para DataFrames grandes

- Métodos administrativos (listar BD, mediciones, campos, tags)- Métodos administrativos (listar BD, mediciones, campos, tags)

- Estadísticas detalladas de escritura- Estadísticas detalladas de escritura



### ⏰ Scheduler### ⏰ Scheduler

Programación y gestión de tareas automatizadas con APScheduler.Programación y gestión de tareas automatizadas con APScheduler.



### 📝 Handler (Logging)## � Instalación

Sistema de logging centralizado con soporte para:

- **Consola y archivos** (con rotación por tamaño/tiempo)```bash

- **Grafana Loki** - Logs centralizados y escalablespip install ctrutils

- **Telegram** - Notificaciones en tiempo real```

- Integración completa con Scheduler e InfluxDB

## 💡 Uso Rápido

## 🚀 Instalación

```python

```bashfrom ctrutils import InfluxdbOperation, Scheduler

pip install ctrutils

# InfluxDB

# Para usar Loki y Telegram:influx = InfluxdbOperation(host='localhost', port=8086)

pip install requestsstats = influx.write_dataframe(

```    measurement='datos',

    data=df,

## 💡 Uso Rápido    validate_data=True  # Limpia NaN automáticamente

)

### InfluxDB

# Scheduler

```pythonscheduler = Scheduler()

from ctrutils import InfluxdbOperationscheduler.add_job(func=mi_funcion, trigger='interval', hours=1)

scheduler.start()

influx = InfluxdbOperation(host='localhost', port=8086)```

stats = influx.write_dataframe(

    measurement='datos',## � Testing

    data=df,

    validate_data=True  # Limpia NaN automáticamenteEl proyecto incluye una suite completa de tests:

)

``````bash

# Ejecutar tests unitarios (rápido, sin dependencias)

### Scheduler con Loggingpytest tests/unit/ -v



```python# Ejecutar tests de integración (requiere InfluxDB)

from ctrutils import Scheduler, LoggingHandlerpytest tests/integration/ -v



logger = LoggingHandler.production_logger(# Ejecutar todos los tests con coverage

    name="scheduler",pytest --cov=ctrutils --cov-report=html

    log_file="scheduler.log",

    loki_url="http://loki:3100",# Usar el script helper

    loki_labels={"app": "myapp", "env": "prod"}./run-tests.sh unit        # Solo unitarios

)./run-tests.sh coverage    # Con coverage

./run-tests.sh html        # Reporte HTML

scheduler = Scheduler(logger=logger)```

scheduler.add_job(

    func=mi_funcion, Para más información sobre tests, ver [tests/README.md](tests/README.md).

    trigger='interval',

    trigger_args={'hours': 1}## 📊 Coverage

)

scheduler.start()El proyecto mantiene >80% de cobertura de código. Ver reporte completo en `htmlcov/` después de ejecutar tests.

```

## �🤝 Contribuciones

### Logger Standalone

¡Las contribuciones son bienvenidas! Si encuentras algún problema o tienes alguna mejora, no dudes en abrir un issue o enviar un pull request.

```python

from ctrutils import LoggingHandler## 📬 Contacto

import logging

Si tienes alguna pregunta o sugerencia, contacta a través de [GitHub](https://github.com/TacoronteRiveroCristian/ctrutils/issues) o mediante el correo electrónico [tacoronteriverocristian@gmail.com](mailto:tacoronteriverocristian@gmail.com).

# Logger rápido de consola

logger = LoggingHandler.quick_console_logger("app", logging.INFO)## 📜 Licencia

logger.info("Hello World")

Este proyecto está bajo la siguiente [licencia](https://github.com/TacoronteRiveroCristian/ctrutils/blob/main/LICENSE).

# Logger completo con múltiples outputs
handler = LoggingHandler()
logger = handler.add_handlers([
    handler.create_stream_handler(),
    handler.create_file_handler("app.log"),
    handler.create_loki_handler(
        url="http://loki:3100",
        labels={"app": "myapp"}
    )
])
```

## 📚 Documentación Handler

Ver [ctrutils/handler/README.md](ctrutils/handler/README.md) para:
- Ejemplos completos de Loki y Telegram
- Integración con Scheduler e InfluxDB
- Configuración de producción
- Troubleshooting

## ✅ Testing

El proyecto incluye una suite completa de tests:

```bash
# Ejecutar tests unitarios (rápido, sin dependencias)
pytest tests/unit/ -v

# Ejecutar tests de integración (requiere InfluxDB)
pytest tests/integration/ -v

# Ejecutar todos los tests con coverage
pytest --cov=ctrutils --cov-report=html

# Usar el script helper
./run-tests.sh unit        # Solo unitarios
./run-tests.sh coverage    # Con coverage
./run-tests.sh html        # Reporte HTML
```

Para más información sobre tests, ver [tests/README.md](tests/README.md).

## 📊 Coverage

El proyecto mantiene >80% de cobertura de código. Ver reporte completo en `htmlcov/` después de ejecutar tests.

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Si encuentras algún problema o tienes alguna mejora, no dudes en abrir un issue o enviar un pull request.

## 📬 Contacto

Si tienes alguna pregunta o sugerencia, contacta a través de [GitHub](https://github.com/TacoronteRiveroCristian/ctrutils/issues) o mediante el correo electrónico [tacoronteriverocristian@gmail.com](mailto:tacoronteriverocristian@gmail.com).

## 📜 Licencia

Este proyecto está bajo la siguiente [licencia](https://github.com/TacoronteRiveroCristian/ctrutils/blob/main/LICENSE).
