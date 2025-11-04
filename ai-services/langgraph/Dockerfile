# LangGraph Server - PATCO ERP
# Dockerfile para Fase 5: LangGraph Core

FROM python:3.11-slim-bullseye

# Metadatos
LABEL maintainer="PATCO Development Team"
LABEL description="LangGraph Server para orquestación conversacional IA"
LABEL version="1.0.0"

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    libpq-dev \
    postgresql-client \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Actualizar pip
RUN pip install --upgrade pip setuptools wheel

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Crear usuario no-root
RUN groupadd -r langgraphuser && useradd -r -g langgraphuser langgraphuser

# Crear directorios necesarios
RUN mkdir -p /app/logs /app/data /app/cache \
    && chown -R langgraphuser:langgraphuser /app

# Copiar código fuente
COPY --chown=langgraphuser:langgraphuser . .

# Configurar permisos de ejecución
RUN chmod +x /app/main.py

# Configurar zona horaria
ENV TZ=America/Lima
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Cambiar a usuario no-root
USER langgraphuser

# Exponer puerto
EXPOSE 8001

# Variables de entorno por defecto
ENV LANGGRAPH_HOST=0.0.0.0
ENV LANGGRAPH_PORT=8001
ENV LANGGRAPH_DEBUG=false
ENV LANGGRAPH_LOG_LEVEL=INFO

# Configurar PYTHONPATH para resolver importaciones
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Comando de inicio
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]