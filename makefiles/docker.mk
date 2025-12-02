# Makefile para Docker y servicios externos
# Incluye: docker-influxdb, docker-influxdb-stop, docker-influxdb-logs

.PHONY: docker-influxdb docker-influxdb-stop docker-influxdb-logs docker-influxdb-restart docker-check

docker-influxdb: ## Iniciar InfluxDB en Docker para tests
	$(call print_blue,🐳 Iniciando InfluxDB 1.8 en Docker...)
	@docker run -d -p 8086:8086 \
		-e INFLUXDB_DB=test_db \
		-e INFLUXDB_ADMIN_USER=admin \
		-e INFLUXDB_ADMIN_PASSWORD=admin \
		--name influxdb-test \
		influxdb:1.8 2>/dev/null || echo "⚠️  Contenedor ya existe"
	@sleep 2
	$(call print_green,✅ InfluxDB iniciado en localhost:8086)
	@echo ""
	@echo "Credenciales:"
	@echo "  Host: localhost"
	@echo "  Port: 8086"
	@echo "  User: admin"
	@echo "  Password: admin"
	@echo "  Database: test_db"
	@echo ""
	@echo "Para detener: make docker-influxdb-stop"

docker-influxdb-stop: ## Detener y eliminar contenedor de InfluxDB
	$(call print_yellow,🛑 Deteniendo InfluxDB...)
	@docker stop influxdb-test 2>/dev/null || true
	@docker rm influxdb-test 2>/dev/null || true
	$(call print_green,✅ InfluxDB detenido)

docker-influxdb-logs: ## Ver logs del contenedor InfluxDB
	@echo "Logs de InfluxDB (Ctrl+C para salir):"
	@echo ""
	@docker logs -f influxdb-test

docker-influxdb-restart: docker-influxdb-stop docker-influxdb ## Reiniciar contenedor InfluxDB
	$(call print_green,✅ InfluxDB reiniciado)

docker-check: ## Verificar si InfluxDB está corriendo
	@echo "Estado de InfluxDB:"
	@docker ps --filter "name=influxdb-test" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "❌ InfluxDB no está corriendo"
	@echo ""
	@curl -s http://localhost:8086/ping > /dev/null 2>&1 && echo "✅ InfluxDB responde en localhost:8086" || echo "❌ InfluxDB no responde"

# InfluxDB Backup Integration Test targets
.PHONY: docker-backup-test docker-backup-test-bg docker-backup-test-stop docker-backup-test-logs docker-backup-test-clean

docker-backup-test: ## Ejecutar test completo de backup de InfluxDB
	$(call print_blue,🧪 Iniciando test de backup de InfluxDB...)
	@cd tests/integration/influxdb_backup_test && chmod +x run_test.sh && ./run_test.sh

docker-backup-test-bg: ## Ejecutar test de backup en background
	$(call print_blue,🧪 Iniciando test de backup en background...)
	@cd tests/integration/influxdb_backup_test && docker-compose up --build -d
	$(call print_green,✅ Contenedores iniciados. Use 'make docker-backup-test-logs' para ver el progreso)

docker-backup-test-stop: ## Detener contenedores del test de backup
	$(call print_yellow,🛑 Deteniendo contenedores del test de backup...)
	@cd tests/integration/influxdb_backup_test && docker-compose down -v
	$(call print_green,✅ Contenedores detenidos)

docker-backup-test-logs: ## Ver logs del test de backup
	@cd tests/integration/influxdb_backup_test && docker-compose logs -f python-generator

docker-backup-test-clean: ## Limpiar datos y logs del test de backup
	$(call print_yellow,🧹 Limpiando datos del test de backup...)
	@cd tests/integration/influxdb_backup_test && rm -rf backup_data/* logs/*
	@$(call print_green,✅ Limpieza completa)
