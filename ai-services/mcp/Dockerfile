# Dockerfile para Servidor MCP
# Basado en Python 3.11 slim para optimizar el tamaño
FROM python:3.11-slim-bullseye

# Metadatos del contenedor
LABEL maintainer="PAT02-ERP Team"
LABEL description="Servidor MCP (Model Context Protocol) para integración con Odoo"
LABEL version="1.0.0"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    # Dependencias básicas
    build-essential \
    curl \
    wget \
    git \
    # Dependencias para PostgreSQL
    libpq-dev \
    postgresql-client \
    # Dependencias para compilación de paquetes Python
    gcc \
    g++ \
    make \
    # Dependencias para procesamiento de archivos
    libmagic1 \
    libmagic-dev \
    # Dependencias para SSL/TLS
    ca-certificates \
    openssl \
    libssl-dev \
    # Dependencias para compresión
    zlib1g-dev \
    libbz2-dev \
    liblzma-dev \
    # Dependencias para XML/HTML
    libxml2-dev \
    libxslt1-dev \
    # Dependencias para imágenes (si es necesario)
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    # Dependencias para networking
    netcat-openbsd \
    # Utilidades del sistema
    procps \
    htop \
    nano \
    vim \
    # Limpieza
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Actualizar pip y instalar herramientas básicas
RUN pip install --upgrade pip setuptools wheel

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Crear usuario no-root para seguridad
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser

# Crear directorios necesarios
RUN mkdir -p /app/logs /app/uploads /app/data /app/cache \
    && chown -R mcpuser:mcpuser /app

# Copiar código fuente
COPY --chown=mcpuser:mcpuser . .

# Configurar permisos
RUN chmod +x /app/server.py

# Configuración de timezone (antes de cambiar a usuario no-root)
ENV TZ=America/Lima
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Cambiar a usuario no-root
USER mcpuser

# Exponer puerto del servidor MCP
EXPOSE 8080

# Variables de entorno por defecto
ENV MCP_HOST=0.0.0.0 \
    MCP_PORT=8080 \
    MCP_DEBUG=false \
    MCP_LOG_LEVEL=INFO \
    MCP_ENVIRONMENT=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Comando por defecto
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]

# Comando alternativo para desarrollo
# CMD ["python", "mcp/server.py"]

# Volúmenes recomendados
VOLUME ["/app/logs", "/app/uploads", "/app/data", "/app/cache"]

# Configuración adicional para producción
# Optimizaciones de memoria y rendimiento
ENV MALLOC_ARENA_MAX=2 \
    MALLOC_MMAP_THRESHOLD_=131072 \
    MALLOC_TRIM_THRESHOLD_=131072 \
    MALLOC_TOP_PAD_=131072 \
    MALLOC_MMAP_MAX_=65536

# Configuración de logging
ENV PYTHONIOENCODING=utf-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Configuración de timezone
ENV TZ=America/Lima

# Configuración de seguridad
# Deshabilitar funciones peligrosas
ENV PYTHONHASHSEED=random

# Configuración de red
# Timeout para conexiones HTTP
ENV HTTP_TIMEOUT=30 \
    CONNECTION_TIMEOUT=10 \
    READ_TIMEOUT=30

# Configuración de base de datos
# Pool de conexiones por defecto
ENV DB_POOL_SIZE=5 \
    DB_MAX_OVERFLOW=10 \
    DB_POOL_TIMEOUT=30 \
    DB_POOL_RECYCLE=3600

# Configuración de cache
ENV CACHE_TTL=3600 \
    CACHE_MAX_SIZE=1000

# Configuración de archivos
ENV MAX_FILE_SIZE=10485760 \
    ALLOWED_FILE_TYPES="txt,pdf,doc,docx,xls,xlsx,png,jpg,jpeg,gif"

# Configuración de rate limiting
ENV RATE_LIMIT_REQUESTS=100 \
    RATE_LIMIT_WINDOW=60

# Configuración de CORS
ENV CORS_ORIGINS="*" \
    CORS_METHODS="GET,POST,PUT,DELETE,OPTIONS" \
    CORS_HEADERS="*"

# Configuración de JWT
ENV JWT_ALGORITHM=HS256 \
    JWT_EXPIRE_MINUTES=1440

# Configuración de embeddings
ENV EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2" \
    EMBEDDING_DIMENSION=384 \
    SIMILARITY_THRESHOLD=0.7

# Configuración de AI/LLM
ENV DEFAULT_AI_MODEL="gpt-4" \
    MAX_TOKENS=4000 \
    TEMPERATURE=0.7

# Configuración de monitoreo
ENV ENABLE_METRICS=true \
    METRICS_PORT=9090 \
    ENABLE_HEALTH_CHECK=true

# Configuración de desarrollo (comentado para producción)
# ENV MCP_DEBUG=true \
#     MCP_LOG_LEVEL=DEBUG \
#     MCP_RELOAD=true

# Etiquetas adicionales para Docker
LABEL org.opencontainers.image.title="MCP Server"
LABEL org.opencontainers.image.description="Servidor MCP para integración con Odoo y servicios de IA"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="PAT02-ERP Team"
LABEL org.opencontainers.image.url="https://github.com/pat02-erp/mcp-server"
LABEL org.opencontainers.image.source="https://github.com/pat02-erp/mcp-server"
LABEL org.opencontainers.image.vendor="PAT02-ERP"
LABEL org.opencontainers.image.licenses="MIT"

# Configuración de señales para graceful shutdown
STOPSIGNAL SIGTERM

# Configuración de límites de recursos (comentado, se configura en docker-compose)
# MEMORY: 512MB
# CPU: 0.5 cores

# Configuración de logging para Docker
# Los logs se envían a stdout/stderr para que Docker los capture
ENV LOG_TO_STDOUT=true \
    LOG_FORMAT=json

# Script de entrada personalizado (opcional)
# COPY docker-entrypoint.sh /usr/local/bin/
# RUN chmod +x /usr/local/bin/docker-entrypoint.sh
# ENTRYPOINT ["docker-entrypoint.sh"]

# Configuración final
WORKDIR /app

# Verificación final de la instalación
RUN python -c "import fastapi, uvicorn, pydantic, psycopg2; print('Dependencias principales instaladas correctamente')"

# Información de construcción
ARG BUILD_DATE
ARG VCS_REF
LABEL org.opencontainers.image.created=$BUILD_DATE
LABEL org.opencontainers.image.revision=$VCS_REF

# Comando de inicio optimizado para producción
CMD ["python", "-m", "uvicorn", "server:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--workers", "1", \
     "--access-log"]

# Configurar PYTHONPATH para resolver importaciones
ENV PYTHONPATH=/app