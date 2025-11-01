# ctrutils

**ctrutils** es una librería minimalista de utilidades en Python enfocada en operaciones con InfluxDB y programación de tareas.

## 📦 Módulos

### 🗄️ InfluxDB Operations
Operaciones avanzadas con InfluxDB incluyendo:
- Validación automática de datos (NaN, infinitos, None)
- Escritura por lotes para DataFrames grandes
- Métodos administrativos (listar BD, mediciones, campos, tags)
- Estadísticas detalladas de escritura

### ⏰ Scheduler
Programación y gestión de tareas automatizadas con APScheduler.

## � Instalación

```bash
pip install ctrutils
```

## 💡 Uso Rápido

```python
from ctrutils import InfluxdbOperation, Scheduler

# InfluxDB
influx = InfluxdbOperation(host='localhost', port=8086)
stats = influx.write_dataframe(
    measurement='datos',
    data=df,
    validate_data=True  # Limpia NaN automáticamente
)

# Scheduler
scheduler = Scheduler()
scheduler.add_job(func=mi_funcion, trigger='interval', hours=1)
scheduler.start()
```

## � Testing

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

## �🤝 Contribuciones

¡Las contribuciones son bienvenidas! Si encuentras algún problema o tienes alguna mejora, no dudes en abrir un issue o enviar un pull request.

## 📬 Contacto

Si tienes alguna pregunta o sugerencia, contacta a través de [GitHub](https://github.com/TacoronteRiveroCristian/ctrutils/issues) o mediante el correo electrónico [tacoronteriverocristian@gmail.com](mailto:tacoronteriverocristian@gmail.com).

## 📜 Licencia

Este proyecto está bajo la siguiente [licencia](https://github.com/TacoronteRiveroCristian/ctrutils/blob/main/LICENSE).
