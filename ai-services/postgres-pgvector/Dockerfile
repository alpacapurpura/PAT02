FROM postgres:15

# Instalar dependencias para compilar pgvector
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    postgresql-server-dev-15 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Compilar e instalar pgvector
RUN git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git \
    && cd pgvector \
    && make \
    && make install \
    && cd .. \
    && rm -rf pgvector

# Verificar que la extensión esté instalada correctamente
RUN ls -la /usr/share/postgresql/15/extension/ | grep vector

# Copiar script de inicialización
COPY init-pgvector.sql /docker-entrypoint-initdb.d/

# Configurar permisos
RUN chmod 644 /docker-entrypoint-initdb.d/init-pgvector.sql