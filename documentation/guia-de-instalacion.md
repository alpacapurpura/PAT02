

# 1. Crear y dar permisos al directorio de logs
sudo mkdir -p /opt/PAT02/logs
sudo chown -R 999:999 /opt/PAT02/logs
sudo chmod -R 755 /opt/PAT02/logs

# 2. Verificar permisos de configuración
sudo chown -R 999:999 /opt/PAT02/config
sudo chmod -R 644 /opt/PAT02/config/*

# 3. Verificar permisos de extra-addons
sudo chown -R 999:999 /opt/PAT02/extra-addons
sudo chmod -R 755 /opt/PAT02/extra-addons

# 4. Verificar permisos del archivo docker-compose.yml
sudo chown root:root /opt/PAT02/docker-compose.yml
sudo chmod 644 /opt/PAT02/docker-compose.yml