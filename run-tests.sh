#!/bin/bash
# Script para ejecutar tests de ctrutils
# Uso: ./run-tests.sh [opciones]

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Funciones de ayuda
print_green() {
    echo -e "${GREEN}$1${NC}"
}

print_yellow() {
    echo -e "${YELLOW}$1${NC}"
}

print_red() {
    echo -e "${RED}$1${NC}"
}

# Banner
echo "================================"
print_green "   ctrutils Test Runner"
echo "================================"
echo ""

# Verificar que pytest este instalado
if ! command -v pytest &> /dev/null; then
    print_red "❌ pytest no esta instalado"
    echo "Instalar con: pip install pytest pytest-cov pytest-mock"
    exit 1
fi

# Funcion para mostrar uso
show_usage() {
    echo "Uso: ./run-tests.sh [opcion]"
    echo ""
    echo "Opciones:"
    echo "  unit          - Ejecutar solo tests unitarios (rapido)"
    echo "  integration   - Ejecutar solo tests de integracion (requiere InfluxDB)"
    echo "  all           - Ejecutar todos los tests"
    echo "  coverage      - Ejecutar tests con reporte de coverage"
    echo "  html          - Generar reporte HTML de coverage"
    echo "  watch         - Ejecutar tests en modo watch (requiere pytest-watch)"
    echo "  clean         - Limpiar archivos de cache y coverage"
    echo "  help          - Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  ./run-tests.sh unit"
    echo "  ./run-tests.sh coverage"
    echo "  ./run-tests.sh integration"
}

# Funcion para limpiar
clean() {
    print_yellow "🧹 Limpiando archivos de cache y coverage..."
    rm -rf .pytest_cache
    rm -rf htmlcov
    rm -rf .coverage
    rm -rf coverage.xml
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    print_green "✅ Limpieza completada"
}

# Funcion para verificar InfluxDB
check_influxdb() {
    print_yellow "🔍 Verificando conexion a InfluxDB..."

    HOST=${INFLUXDB_TEST_HOST:-localhost}
    PORT=${INFLUXDB_TEST_PORT:-8086}

    if curl -s "http://${HOST}:${PORT}/ping" > /dev/null 2>&1; then
        print_green "✅ InfluxDB disponible en ${HOST}:${PORT}"
        return 0
    else
        print_red "❌ InfluxDB no disponible en ${HOST}:${PORT}"
        echo ""
        echo "Para ejecutar tests de integracion, iniciar InfluxDB:"
        echo ""
        echo "  docker run -d -p 8086:8086 \\"
        echo "    -e INFLUXDB_DB=test_db \\"
        echo "    -e INFLUXDB_ADMIN_USER=admin \\"
        echo "    -e INFLUXDB_ADMIN_PASSWORD=admin \\"
        echo "    --name influxdb-test \\"
        echo "    influxdb:1.8"
        echo ""
        return 1
    fi
}

# Parsear argumentos
COMMAND=${1:-all}

case $COMMAND in
    unit)
        print_yellow "🧪 Ejecutando tests unitarios..."
        pytest tests/unit/ -v --tb=short
        ;;

    integration)
        check_influxdb || exit 1
        print_yellow "🧪 Ejecutando tests de integracion..."
        pytest tests/integration/ -v --tb=short
        ;;

    all)
        print_yellow "🧪 Ejecutando todos los tests..."
        pytest tests/ -v --tb=short
        ;;

    coverage)
        print_yellow "🧪 Ejecutando tests con coverage..."
        pytest tests/ -v --cov=ctrutils --cov-report=term-missing --cov-report=xml
        ;;

    html)
        print_yellow "🧪 Generando reporte HTML de coverage..."
        pytest tests/ -v --cov=ctrutils --cov-report=html --cov-report=term
        print_green "✅ Reporte generado en: htmlcov/index.html"

        # Intentar abrir el reporte
        if command -v xdg-open &> /dev/null; then
            xdg-open htmlcov/index.html 2>/dev/null
        elif command -v open &> /dev/null; then
            open htmlcov/index.html
        fi
        ;;

    watch)
        if ! command -v pytest-watch &> /dev/null; then
            print_red "❌ pytest-watch no esta instalado"
            echo "Instalar con: pip install pytest-watch"
            exit 1
        fi
        print_yellow "👀 Ejecutando tests en modo watch..."
        ptw tests/unit/ -- -v
        ;;

    clean)
        clean
        ;;

    help)
        show_usage
        ;;

    *)
        print_red "❌ Opcion no reconocida: $COMMAND"
        echo ""
        show_usage
        exit 1
        ;;
esac

# Mostrar estadisticas finales
if [ $? -eq 0 ]; then
    echo ""
    print_green "✅ Tests completados exitosamente"
else
    echo ""
    print_red "❌ Algunos tests fallaron"
    exit 1
fi
