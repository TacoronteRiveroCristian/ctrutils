# Documentación ctrutils

Este directorio contiene toda la documentación del proyecto ctrutils.

## Guías Principales

- **[Quick Start](QUICK_START.md)** - Guía de inicio rápido para empezar a usar ctrutils
- **[Project Structure](PROJECT_STRUCTURE.md)** - Arquitectura y decisiones de diseño del proyecto
- **[Test Summary](TEST_SUMMARY.md)** - Guía completa de testing y cobertura

## Documentación de Módulos

### Scheduler
- **[Scheduler README](../ctrutils/scheduler/README.md)** - Documentación completa del módulo scheduler
- **[Scheduler Cheat Sheet](scheduler/SCHEDULER_CHEATSHEET.md)** - Referencia rápida de comandos comunes

### Handler
- **[Handler README](../ctrutils/handler/README.md)** - Sistema de logging y notificaciones

### Database
- **[InfluxDB Operations](../ctrutils/database/influxdb/)** - Módulo de operaciones con InfluxDB

## Herramientas de Desarrollo

- **[Makefile Commands](../makefiles/README.md)** - Comandos disponibles para desarrollo, testing y deployment

## Estructura de Documentación

```
docs/
├── PROJECT_STRUCTURE.md    # Arquitectura del proyecto
├── QUICK_START.md          # Guía de inicio rápido
├── TEST_SUMMARY.md         # Documentación de tests
├── README.md               # Este archivo (índice)
└── scheduler/              # Docs específicas del scheduler
    └── SCHEDULER_CHEATSHEET.md
```

## Documentación en el Código

Cada módulo tiene su propio README en su directorio:
- `ctrutils/scheduler/README.md` - Documentación completa del scheduler
- `ctrutils/handler/README.md` - Documentación del sistema de handlers

## Enlaces Externos

- **[README Principal](../README.md)** - Información general del proyecto
- **[CHANGELOG](../CHANGELOG.md)** - Historial de cambios y versiones
- **[CONTRIBUTING](../CONTRIBUTING.md)** - Guía de contribución

## Recursos Adicionales

- **[GitHub Repository](https://github.com/TacoronteRiveroCristian/ctrutils)** - Repositorio del código fuente
- **[PyPI Package](https://pypi.org/project/ctrutils/)** - Paquete publicado

---

**Versión**: 11.0.0
**Última actualización**: Noviembre 2025
