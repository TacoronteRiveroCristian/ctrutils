# InfluxDB Backup Integration Test

Sistema completo de pruebas para validar el módulo de backup/restore de InfluxDB de ctrutils.

## Descripción

Este sistema genera datos heterogéneos en múltiples databases y measurements, realiza backup del origen (puerto 48086) al destino (puerto 68086), y valida la integridad de los datos con análisis estadístico detallado.

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Network                           │
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │  InfluxDB    │         │  InfluxDB    │                  │
│  │   ORIGEN     │         │   DESTINO    │                  │
│  │ Port: 48086  │         │ Port: 68086  │                  │
│  └──────────────┘         └──────────────┘                  │
│         ▲                          ▲                         │
│         │    ┌──────────────┐     │                         │
│         └────│   Python     │─────┘                         │
│              │  Generator   │                                │
│              └──────────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

## Datos Generados

- **4 Databases:**
  - `iot_sensors` - 6 measurements (sensores IoT)
  - `app_metrics` - 7 measurements (métricas de aplicación)
  - `industrial_monitoring` - 5 measurements (monitoreo industrial)
  - `smart_building` - 7 measurements (edificio inteligente)

- **Total: ~25 measurements** con datos heterogéneos
- **Generación inicial:** 2 horas de datos históricos
- **Tipos de datos:** float, int con valores realistas
- **Tags variados:** ubicaciones, tipos, entornos, etc.

## Uso

### Ejecución básica

```bash
cd tests/integration/influxdb_backup_test
./run_test.sh
```

### Con make (desde raíz del proyecto)

```bash
make docker-backup-test          # Ejecutar test completo
make docker-backup-test-bg       # Ejecutar en background
make docker-backup-test-logs     # Ver logs en tiempo real
make docker-backup-test-stop     # Detener contenedores
make docker-backup-test-clean    # Limpiar datos y logs
```

## Workflow de Prueba

1. **Fase 1:** Generación de datos iniciales en origen (48086)
2. **Fase 2:** Backup de todas las databases a CSV
3. **Fase 3:** Restore al destino (68086)
4. **Fase 4:** Validación de integridad con estadísticas
5. **Fase 5:** (Opcional) Generación continua para simular producción

## Salidas

- **Logs:** `logs/backup_test.log`
- **Reporte JSON:** `logs/test_report.json`
- **Archivos CSV:** `backup_data/*.csv`

## Validación

El test verifica:
- Count de puntos por measurement (tolerancia 1%)
- Lista de databases y measurements coinciden
- Integridad de datos entre origen y destino

## Requisitos

- Docker y Docker Compose
- Puertos 48086 y 68086 disponibles
- ~2GB de espacio en disco

## Configuración

Editar variables en `docker-compose.yml`:
- `INITIAL_HOURS`: Horas de datos históricos (default: 2)
- `CONTINUOUS_GENERATION`: Generar datos continuos (default: false)
- `GENERATION_INTERVAL`: Intervalo de generación en segundos (default: 10)
- `TEST_DURATION`: Duración de generación continua (default: 300s)
