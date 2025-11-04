# Makefile para el Servidor MCP
# =============================
# 
# Este Makefile automatiza las tareas comunes de desarrollo,
# testing y despliegue del servidor MCP.
#
# Autor: PATCO Development Team
# Versión: 1.0.0
# Fecha: Enero 2025

# Variables
PYTHON := python
PIP := pip
PYTEST := pytest
DOCKER := docker
DOCKER_COMPOSE := docker-compose
PROJECT_NAME := mcp-server
IMAGE_NAME := patco/mcp-server
CONTAINER_NAME := mcp-server
PORT := 8080

# Colores para output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Ayuda por defecto
.DEFAULT_GOAL := help

.PHONY: help
help: ## Mostrar esta ayuda
	@echo "$(BLUE)Makefile para el Servidor MCP$(NC)"
	@echo "$(BLUE)==============================$(NC)"
	@echo ""
	@echo "$(YELLOW)Comandos disponibles:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Ejemplos de uso:$(NC)"
	@echo "  make install          # Instalar dependencias"
	@echo "  make test             # Ejecutar todos los tests"
	@echo "  make test-unit        # Solo tests unitarios"
	@echo "  make run              # Ejecutar servidor en desarrollo"
	@echo "  make docker-build     # Construir imagen Docker"
	@echo "  make docker-run       # Ejecutar en Docker"
	@echo "  make lint             # Verificar código"
	@echo "  make format           # Formatear código"
	@echo "  make clean            # Limpiar archivos temporales"

# ============================================================================
# DESARROLLO LOCAL
# ============================================================================

.PHONY: install
install: ## Instalar dependencias de desarrollo
	@echo "$(YELLOW)Instalando dependencias...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt
	@echo "$(GREEN)✓ Dependencias instaladas$(NC)"

.PHONY: install-dev
install-dev: ## Instalar dependencias de desarrollo adicionales
	@echo "$(YELLOW)Instalando dependencias de desarrollo...$(NC)"
	$(PIP) install pytest pytest-asyncio pytest-cov pytest-mock pytest-timeout
	$(PIP) install black flake8 isort mypy pylint
	$(PIP) install pre-commit
	@echo "$(GREEN)✓ Dependencias de desarrollo instaladas$(NC)"

.PHONY: setup
setup: install install-dev ## Configuración inicial completa
	@echo "$(YELLOW)Configurando pre-commit hooks...$(NC)"
	pre-commit install
	@echo "$(GREEN)✓ Configuración inicial completada$(NC)"

.PHONY: run
run: ## Ejecutar servidor en modo desarrollo
	@echo "$(YELLOW)Iniciando servidor MCP en modo desarrollo...$(NC)"
	@echo "$(BLUE)Servidor disponible en: http://localhost:$(PORT)$(NC)"
	$(PYTHON) server.py

.PHONY: run-prod
run-prod: ## Ejecutar servidor en modo producción
	@echo "$(YELLOW)Iniciando servidor MCP en modo producción...$(NC)"
	MCP_ENVIRONMENT=production $(PYTHON) server.py

# ============================================================================
# TESTING
# ============================================================================

.PHONY: test
test: ## Ejecutar todos los tests
	@echo "$(YELLOW)Ejecutando todos los tests...$(NC)"
	$(PYTEST)
	@echo "$(GREEN)✓ Tests completados$(NC)"

.PHONY: test-unit
test-unit: ## Ejecutar solo tests unitarios
	@echo "$(YELLOW)Ejecutando tests unitarios...$(NC)"
	$(PYTEST) -m unit
	@echo "$(GREEN)✓ Tests unitarios completados$(NC)"

.PHONY: test-integration
test-integration: ## Ejecutar tests de integración
	@echo "$(YELLOW)Ejecutando tests de integración...$(NC)"
	$(PYTEST) -m integration
	@echo "$(GREEN)✓ Tests de integración completados$(NC)"

.PHONY: test-security
test-security: ## Ejecutar tests de seguridad
	@echo "$(YELLOW)Ejecutando tests de seguridad...$(NC)"
	$(PYTEST) -m security
	@echo "$(GREEN)✓ Tests de seguridad completados$(NC)"

.PHONY: test-performance
test-performance: ## Ejecutar tests de rendimiento
	@echo "$(YELLOW)Ejecutando tests de rendimiento...$(NC)"
	$(PYTEST) -m performance
	@echo "$(GREEN)✓ Tests de rendimiento completados$(NC)"

.PHONY: test-fast
test-fast: ## Ejecutar tests rápidos (excluir lentos)
	@echo "$(YELLOW)Ejecutando tests rápidos...$(NC)"
	$(PYTEST) -m "not slow"
	@echo "$(GREEN)✓ Tests rápidos completados$(NC)"

.PHONY: test-coverage
test-coverage: ## Ejecutar tests con reporte de cobertura
	@echo "$(YELLOW)Ejecutando tests con cobertura...$(NC)"
	$(PYTEST) --cov=. --cov-report=html --cov-report=term
	@echo "$(GREEN)✓ Tests con cobertura completados$(NC)"
	@echo "$(BLUE)Reporte HTML disponible en: htmlcov/index.html$(NC)"

.PHONY: test-watch
test-watch: ## Ejecutar tests en modo watch (requiere pytest-watch)
	@echo "$(YELLOW)Ejecutando tests en modo watch...$(NC)"
	ptw -- --tb=short

# ============================================================================
# CALIDAD DE CÓDIGO
# ============================================================================

.PHONY: lint
lint: ## Verificar calidad del código
	@echo "$(YELLOW)Verificando calidad del código...$(NC)"
	@echo "$(BLUE)Ejecutando flake8...$(NC)"
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	@echo "$(BLUE)Ejecutando pylint...$(NC)"
	pylint **/*.py || true
	@echo "$(BLUE)Ejecutando mypy...$(NC)"
	mypy . || true
	@echo "$(GREEN)✓ Verificación de calidad completada$(NC)"

.PHONY: format
format: ## Formatear código automáticamente
	@echo "$(YELLOW)Formateando código...$(NC)"
	@echo "$(BLUE)Ejecutando isort...$(NC)"
	isort .
	@echo "$(BLUE)Ejecutando black...$(NC)"
	black .
	@echo "$(GREEN)✓ Código formateado$(NC)"

.PHONY: format-check
format-check: ## Verificar formato sin modificar archivos
	@echo "$(YELLOW)Verificando formato del código...$(NC)"
	isort --check-only .
	black --check .
	@echo "$(GREEN)✓ Formato verificado$(NC)"

.PHONY: security-check
security-check: ## Verificar vulnerabilidades de seguridad
	@echo "$(YELLOW)Verificando vulnerabilidades de seguridad...$(NC)"
	bandit -r . -f json -o security-report.json || true
	safety check
	@echo "$(GREEN)✓ Verificación de seguridad completada$(NC)"

# ============================================================================
# DOCKER
# ============================================================================

.PHONY: docker-build
docker-build: ## Construir imagen Docker
	@echo "$(YELLOW)Construyendo imagen Docker...$(NC)"
	$(DOCKER) build -t $(IMAGE_NAME):latest .
	@echo "$(GREEN)✓ Imagen Docker construida: $(IMAGE_NAME):latest$(NC)"

.PHONY: docker-build-dev
docker-build-dev: ## Construir imagen Docker para desarrollo
	@echo "$(YELLOW)Construyendo imagen Docker para desarrollo...$(NC)"
	$(DOCKER) build -f Dockerfile.dev -t $(IMAGE_NAME):dev .
	@echo "$(GREEN)✓ Imagen Docker de desarrollo construida: $(IMAGE_NAME):dev$(NC)"

.PHONY: docker-run
docker-run: ## Ejecutar contenedor Docker
	@echo "$(YELLOW)Ejecutando contenedor Docker...$(NC)"
	$(DOCKER) run -d --name $(CONTAINER_NAME) -p $(PORT):$(PORT) $(IMAGE_NAME):latest
	@echo "$(GREEN)✓ Contenedor ejecutándose en: http://localhost:$(PORT)$(NC)"

.PHONY: docker-run-dev
docker-run-dev: ## Ejecutar contenedor Docker en modo desarrollo
	@echo "$(YELLOW)Ejecutando contenedor Docker en modo desarrollo...$(NC)"
	$(DOCKER) run -it --rm --name $(CONTAINER_NAME)-dev \
		-p $(PORT):$(PORT) \
		-v $(PWD):/app \
		-e MCP_ENVIRONMENT=development \
		$(IMAGE_NAME):dev

.PHONY: docker-stop
docker-stop: ## Detener contenedor Docker
	@echo "$(YELLOW)Deteniendo contenedor Docker...$(NC)"
	$(DOCKER) stop $(CONTAINER_NAME) || true
	$(DOCKER) rm $(CONTAINER_NAME) || true
	@echo "$(GREEN)✓ Contenedor detenido$(NC)"

.PHONY: docker-logs
docker-logs: ## Ver logs del contenedor Docker
	@echo "$(YELLOW)Mostrando logs del contenedor...$(NC)"
	$(DOCKER) logs -f $(CONTAINER_NAME)

.PHONY: docker-shell
docker-shell: ## Acceder al shell del contenedor Docker
	@echo "$(YELLOW)Accediendo al shell del contenedor...$(NC)"
	$(DOCKER) exec -it $(CONTAINER_NAME) /bin/bash

# ============================================================================
# DOCKER COMPOSE
# ============================================================================

.PHONY: compose-up
compose-up: ## Levantar servicios con docker-compose
	@echo "$(YELLOW)Levantando servicios con docker-compose...$(NC)"
	cd ../.. && $(DOCKER_COMPOSE) up -d --profile ai-services
	@echo "$(GREEN)✓ Servicios levantados$(NC)"

.PHONY: compose-down
compose-down: ## Bajar servicios con docker-compose
	@echo "$(YELLOW)Bajando servicios con docker-compose...$(NC)"
	cd ../.. && $(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓ Servicios bajados$(NC)"

.PHONY: compose-logs
compose-logs: ## Ver logs de docker-compose
	@echo "$(YELLOW)Mostrando logs de docker-compose...$(NC)"
	cd ../.. && $(DOCKER_COMPOSE) logs -f mcp-server

.PHONY: compose-restart
compose-restart: ## Reiniciar servicio MCP en docker-compose
	@echo "$(YELLOW)Reiniciando servicio MCP...$(NC)"
	cd ../.. && $(DOCKER_COMPOSE) restart mcp-server
	@echo "$(GREEN)✓ Servicio MCP reiniciado$(NC)"

# ============================================================================
# UTILIDADES
# ============================================================================

.PHONY: clean
clean: ## Limpiar archivos temporales y cache
	@echo "$(YELLOW)Limpiando archivos temporales...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf security-report.json
	rm -rf .mypy_cache
	rm -rf dist
	rm -rf build
	@echo "$(GREEN)✓ Archivos temporales eliminados$(NC)"

.PHONY: clean-docker
clean-docker: ## Limpiar imágenes y contenedores Docker
	@echo "$(YELLOW)Limpiando Docker...$(NC)"
	$(DOCKER) system prune -f
	$(DOCKER) image prune -f
	@echo "$(GREEN)✓ Docker limpiado$(NC)"

.PHONY: logs
logs: ## Ver logs del servidor
	@echo "$(YELLOW)Mostrando logs del servidor...$(NC)"
	tail -f logs/mcp-server.log 2>/dev/null || echo "$(RED)No se encontraron logs$(NC)"

.PHONY: health
health: ## Verificar salud del servidor
	@echo "$(YELLOW)Verificando salud del servidor...$(NC)"
	curl -f http://localhost:$(PORT)/health || echo "$(RED)Servidor no disponible$(NC)"

.PHONY: status
status: ## Mostrar estado de servicios
	@echo "$(YELLOW)Estado de servicios:$(NC)"
	@echo "$(BLUE)Docker containers:$(NC)"
	$(DOCKER) ps --filter name=$(CONTAINER_NAME)
	@echo "$(BLUE)Docker compose services:$(NC)"
	cd ../.. && $(DOCKER_COMPOSE) ps

.PHONY: env-check
env-check: ## Verificar variables de entorno
	@echo "$(YELLOW)Verificando variables de entorno...$(NC)"
	$(PYTHON) -c "from config import MCPConfig; config = MCPConfig(); print('✓ Configuración válida')"
	@echo "$(GREEN)✓ Variables de entorno verificadas$(NC)"

.PHONY: deps-check
deps-check: ## Verificar dependencias
	@echo "$(YELLOW)Verificando dependencias...$(NC)"
	$(PIP) check
	@echo "$(GREEN)✓ Dependencias verificadas$(NC)"

# ============================================================================
# DOCUMENTACIÓN
# ============================================================================

.PHONY: docs
docs: ## Generar documentación
	@echo "$(YELLOW)Generando documentación...$(NC)"
	@echo "$(BLUE)Estructura del proyecto:$(NC)"
	tree -I '__pycache__|*.pyc|.git|.pytest_cache|htmlcov' .
	@echo "$(GREEN)✓ Documentación generada$(NC)"

.PHONY: api-docs
api-docs: ## Generar documentación de API
	@echo "$(YELLOW)Generando documentación de API...$(NC)"
	@echo "$(BLUE)Documentación disponible en: http://localhost:$(PORT)/docs$(NC)"
	@echo "$(BLUE)OpenAPI spec disponible en: http://localhost:$(PORT)/openapi.json$(NC)"

# ============================================================================
# DESARROLLO Y DEBUGGING
# ============================================================================

.PHONY: debug
debug: ## Ejecutar servidor en modo debug
	@echo "$(YELLOW)Ejecutando servidor en modo debug...$(NC)"
	MCP_DEBUG=true MCP_LOG_LEVEL=DEBUG $(PYTHON) server.py

.PHONY: shell
shell: ## Abrir shell interactivo de Python
	@echo "$(YELLOW)Abriendo shell interactivo...$(NC)"
	$(PYTHON) -i -c "from config import MCPConfig; from utils import *; config = MCPConfig(); print('Entorno MCP cargado')"

.PHONY: profile
profile: ## Ejecutar profiling del servidor
	@echo "$(YELLOW)Ejecutando profiling...$(NC)"
	$(PYTHON) -m cProfile -o profile.stats server.py
	@echo "$(GREEN)✓ Profiling completado: profile.stats$(NC)"

# ============================================================================
# CI/CD
# ============================================================================

.PHONY: ci
ci: clean format-check lint test-coverage security-check ## Pipeline completo de CI
	@echo "$(GREEN)✓ Pipeline de CI completado$(NC)"

.PHONY: pre-commit
pre-commit: format lint test-fast ## Verificaciones antes de commit
	@echo "$(GREEN)✓ Verificaciones pre-commit completadas$(NC)"

.PHONY: release-check
release-check: ci docker-build ## Verificaciones antes de release
	@echo "$(GREEN)✓ Verificaciones de release completadas$(NC)"

# ============================================================================
# INFORMACIÓN
# ============================================================================

.PHONY: info
info: ## Mostrar información del proyecto
	@echo "$(BLUE)Información del Proyecto$(NC)"
	@echo "$(BLUE)========================$(NC)"
	@echo "Proyecto: $(PROJECT_NAME)"
	@echo "Imagen Docker: $(IMAGE_NAME)"
	@echo "Puerto: $(PORT)"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Pip: $(shell $(PIP) --version)"
	@echo "Docker: $(shell $(DOCKER) --version)"
	@echo "Docker Compose: $(shell $(DOCKER_COMPOSE) --version)"
	@echo ""
	@echo "$(YELLOW)Archivos de configuración:$(NC)"
	@ls -la *.py *.ini *.txt Dockerfile* 2>/dev/null || true

.PHONY: version
version: ## Mostrar versión del proyecto
	@echo "$(BLUE)Versión del Servidor MCP: 1.0.0$(NC)"

# Verificar que los comandos necesarios estén disponibles
.PHONY: check-deps
check-deps: ## Verificar dependencias del sistema
	@echo "$(YELLOW)Verificando dependencias del sistema...$(NC)"
	@command -v $(PYTHON) >/dev/null 2>&1 || { echo "$(RED)Python no encontrado$(NC)"; exit 1; }
	@command -v $(PIP) >/dev/null 2>&1 || { echo "$(RED)Pip no encontrado$(NC)"; exit 1; }
	@command -v $(DOCKER) >/dev/null 2>&1 || { echo "$(RED)Docker no encontrado$(NC)"; exit 1; }
	@command -v $(DOCKER_COMPOSE) >/dev/null 2>&1 || { echo "$(RED)Docker Compose no encontrado$(NC)"; exit 1; }
	@echo "$(GREEN)✓ Todas las dependencias están disponibles$(NC)"