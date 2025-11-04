# PATCO AI Agent - Document Indexer Service
# Dockerfile para el servicio de indexación de documentos

FROM python:3.11-slim

# Metadatos
LABEL maintainer="PATCO Development Team"
LABEL description="Document Indexer Service for PATCO AI Agent"
LABEL version="1.0.0"

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    # Compiladores y herramientas de desarrollo
    gcc \
    g++ \
    make \
    # PostgreSQL client libraries
    libpq-dev \
    # Tesseract OCR
    tesseract-ocr \
    tesseract-ocr-spa \
    tesseract-ocr-eng \
    # Librerías para procesamiento de imágenes
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    # Utilidades
    curl \
    # Limpiar cache
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Crear usuario no-root para seguridad
RUN groupadd -r indexer && useradd -r -g indexer indexer

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear directorio para logs
RUN mkdir -p /app/logs && chown -R indexer:indexer /app

# Cambiar a usuario no-root
USER indexer

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import psycopg2; print('OK')" || exit 1

# Comando por defecto
CMD ["python", "indexer.py", "--watch"]