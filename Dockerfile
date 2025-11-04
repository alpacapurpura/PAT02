# Dockerfile para Odoo Community 18 usando código fuente local
FROM python:3.11-slim-bullseye

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    libldap2-dev \
    libsasl2-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev \
    pkg-config \
    postgresql-client \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    wkhtmltopdf \
    xfonts-75dpi \
    xfonts-base \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario odoo
RUN useradd -ms /bin/bash odoo

# Crear directorios necesarios
RUN mkdir -p /opt/odoo \
    && mkdir -p /var/lib/odoo \
    && mkdir -p /etc/odoo \
    && chown -R odoo:odoo /opt/odoo \
    && chown -R odoo:odoo /var/lib/odoo \
    && chown -R odoo:odoo /etc/odoo

# Cambiar al usuario odoo
USER odoo

# Establecer directorio de trabajo
WORKDIR /opt/odoo

# Copiar el código fuente de Odoo
COPY --chown=odoo:odoo . /opt/odoo/

# Instalar dependencias de Python
RUN pip3 install --user -r requirements.txt

# Configurar variables de entorno
ENV PATH="/home/odoo/.local/bin:$PATH"
ENV PYTHONPATH="/opt/odoo:$PYTHONPATH"

# Exponer puerto
EXPOSE 8069

# Comando por defecto
CMD ["python3", "/opt/odoo/odoo-bin", "-c", "/etc/odoo/odoo.conf"]