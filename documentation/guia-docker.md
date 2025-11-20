# 🐳 Guía de Gestión Docker - Proyecto PATCO

## 📋 Índice
1. [Resumen de Problemas Comunes](#resumen-de-problemas-comunes)
2. [Gestión Básica por Ambientes](#gestión-básica-por-ambientes)
3. [Gestión de Base de Datos](#gestión-de-base-de-datos)
4. [Limpieza y Reseteo](#limpieza-y-reseteo)
5. [Diagnóstico y Logs](#diagnóstico-y-logs)
6. [Solución de Problemas Específicos](#solución-de-problemas-específicos)
7. [Referencia de Servicios](#referencia-de-servicios)

limpiar assets
http://patco.192.168.18.190.nip.io/web?debug=assets
---
Instalar un módulo en DEV desde comandos

docker compose --profile patco-dev run --rm odoo-patco-dev python3 /opt/odoo/odoo-bin -c /etc/odoo/odoo.conf -d odoo_patco -u patco_equipment --db_host=db-dev --db_port=5432 --db_user=odoo --db_password=P4tc0_2 --without-demo=all --stop-after-init && docker compose --profile patco-dev restart odoo-patco-dev

Desarrollo (PATCO)

- Instalar módulo nuevo: 
docker compose --profile patco-dev run --rm odoo-patco-dev python3 /opt/odoo/odoo-bin -c /etc/odoo/odoo.conf -d odoo_patco -i <modulo> --db_host=db-dev --db_port=5432 --db_user=odoo --db_password=P4tc0_2 --stop-after-init
- Actualizar módulo existente: 
docker compose --profile patco-dev run --rm odoo-patco-dev python3 /opt/odoo/odoo-bin -c /etc/odoo/odoo.conf -d odoo_patco -u <modulo> --db_host=db-dev --db_port=5432 --db_user=odoo --db_password=P4tc0_2 --stop-after-init


Producción (PATCO)

- Instalar módulo nuevo: docker compose --profile patco-prod run --rm odoo-patco-prod python3 /opt/odoo/odoo-bin -c /etc/odoo/odoo.conf -d odoo_patco -i <modulo> --db_host=db-prod --db_port=5432 --db_user=odoo --db_password=P4tc0_2 --stop-after-init
- Actualizar módulo existente: docker compose --profile patco-prod run --rm odoo-patco-prod python3 /opt/odoo/odoo-bin -c /etc/odoo/odoo.conf -d odoo_patco -u <modulo> --db_host=db-prod --db_port=5432 --db_user=odoo --db_password=P4tc0_2 --stop-after-init


Desarrollo (ANDESSUYO)

- Instalar módulo nuevo: docker compose --profile andessuyo-dev run --rm odoo-andessuyo-dev python3 /opt/odoo/odoo-bin -c /etc/odoo/odoo.conf -d odoo_andessuyo -i <modulo> --db_host=db-dev --db_port=5432 --db_user=odoo --db_password=P4tc0_2 --stop-after-init
- Actualizar módulo existente: docker compose --profile andessuyo-dev run --rm odoo-andessuyo-dev python3 /opt/odoo/odoo-bin -c /etc/odoo/odoo.conf -d odoo_andessuyo -u <modulo> --db_host=db-dev --db_port=5432 --db_user=odoo --db_password=P4tc0_2 --stop-after-init
Producción (ANDESSUYO)

- Instalar módulo nuevo: docker compose --profile andessuyo-prod run --rm odoo-andessuyo-prod python3 /opt/odoo/odoo-bin -c /etc/odoo/odoo.conf -d odoo_andessuyo -i <modulo> --db_host=db-prod --db_port=5432 --db_user=odoo --db_password=P4tc0_2 --stop-after-init
- Actualizar módulo existente: docker compose --profile andessuyo-prod run --rm odoo-andessuyo-prod python3 /opt/odoo/odoo-bin -c /etc/odoo/odoo.conf -d odoo_andessuyo -u <modulo> --db_host=db-prod --db_port=5432 --db_user=odoo --db_password=P4tc0_2 --stop-after-init


## 📌 Resumen de Problemas Comunes

### ❌ Problema: `docker compose down` no detiene todos los servicios
**Causa**: Los servicios con `profiles` (development/production) no se incluyen en el comando básico.

**Solución**: Usar comandos específicos por perfil.

### ❌ Problema: Error "Resource is still in use" al eliminar redes
**Causa**: Contenedores individuales quedan conectados a la red sin aparecer en `docker ps`.

**Solución**: Inspeccionar la red y eliminar contenedores manualmente.

---

## 🚀 Gestión Básica por Ambientes

### Development (Local)

```bash
# INICIAR servicios de development
docker compose --profile development up -d

# DETENER servicios de development
docker compose --profile development down

# DETENER y ELIMINAR volúmenes (development)
docker compose --profile development down -v

# REINICIAR servicios de development
docker compose --profile development restart

# VER estado de servicios
docker compose --profile development ps
```

### Production (Servidor)

```bash
# INICIAR servicios de production
docker compose --profile production up -d

# DETENER servicios de production
docker compose --profile production down

# DETENER y ELIMINAR volúmenes (production)
docker compose --profile production down -v

# REINICIAR servicios de production
docker compose --profile production restart

# VER estado de servicios
docker compose --profile production ps
```

### Ambos Ambientes

```bash
# INICIAR todos los servicios
docker compose --profile development --profile production up -d

# DETENER todos los servicios
docker compose --profile development --profile production down

# DETENER todos y ELIMINAR volúmenes
docker compose --profile development --profile production down -v
```

---

## 🗄️ Gestión de Base de Datos

### Development - Base de datos `odoo_patco`

```bash
# ACCEDER a PostgreSQL
docker compose exec db-dev psql -U odoo -d odoo_patco

# HACER BACKUP de la base de datos
docker compose exec db-dev pg_dump -U odoo odoo_patco > backup_dev_$(date +%Y%m%d_%H%M%S).sql

# RESTAURAR base de datos desde archivo
docker compose exec -T db-dev psql -U odoo odoo_patco < backup_file.sql

# LIMPIAR assets corruptos (CSS/JS)
docker compose exec db-dev psql -U odoo -d odoo_patco -c "DELETE FROM ir_attachment WHERE res_model = 'ir.ui.view' AND (name ILIKE '%.assets_%.css' OR name ILIKE '%.assets_%.js');"
# Andessuyo PROD
docker compose exec db-prod psql -U odoo -d odoo_andessuyo -c "DELETE FROM ir_attachment WHERE res_model = 'ir.ui.view' AND (name ILIKE '%.assets_%.css' OR name ILIKE '%.assets_%.js');"
# PATCO PROD
docker compose exec db-prod psql -U odoo -d odoo_patco -c "DELETE FROM ir_attachment WHERE res_model = 'ir.ui.view' AND (name ILIKE '%.assets_%.css' OR name ILIKE '%.assets_%.js');"

# REINICIAR Odoo después de limpiar assets
docker compose --profile development restart odoo-patco-dev
```

### Production - Base de datos `odoo_patco`

```bash
# ACCEDER a PostgreSQL (solo diagnóstico)
docker compose --profile production exec db-prod psql -U odoo -d odoo_patco

# HACER BACKUP de la base de datos
docker compose --profile production exec db-prod pg_dump -U odoo odoo_patco > backup_prod_$(date +%Y%m%d_%H%M%S).sql

# RESTAURAR base de datos desde archivo
docker compose --profile production exec -T db-prod psql -U odoo odoo_patco < backup_file.sql

# LIMPIAR assets corruptos (CSS/JS)
docker compose --profile production exec db-prod psql -U odoo -d odoo_patco -c "DELETE FROM ir_attachment WHERE res_model = 'ir.ui.view' AND (name ILIKE '%.assets_%.css' OR name ILIKE '%.assets_%.js');"

# REINICIAR Odoo después de limpiar assets
docker compose --profile production restart odoo-patco-prod
```

---

## 🧹 Limpieza y Reseteo

### Reset Completo - Development

```bash
# 1. Detener todos los servicios y eliminar volúmenes
docker compose --profile development down -v

# 2. Verificar que no queden contenedores
docker ps -a | grep -E "(patco|andessuyo|odoo)"

# 3. Limpiar contenedores huérfanos
docker container prune -f

# 4. Limpiar redes no utilizadas (si es necesario)
docker network prune -f

# 5. Reiniciar desde cero
docker compose --profile development up -d
```

### Reset Completo - Production

```bash
# 1. Detener todos los servicios y eliminar volúmenes
docker compose --profile production down -v

# 2. Verificar que no queden contenedores
docker ps -a | grep -E "(patco|andessuyo|odoo)"

# 3. Limpiar contenedores huérfanos
docker container prune -f

# 4. Reiniciar desde cero
docker compose --profile production up -d
```

### Solución: Red "Resource is still in use"

```bash
# Development
docker network inspect odoo-network-dev
docker stop $(docker network inspect odoo-network-dev -f '{{range .Containers}}{{.Name}} {{end}}')
docker network rm odoo-network-dev

# Production
docker network inspect odoo-patco-network-prod
docker stop $(docker network inspect odoo-patco-network-prod -f '{{range .Containers}}{{.Name}} {{end}}')
docker network rm odoo-patco-network-prod
```

---

## 🔍 Diagnóstico y Logs

### Ver Logs por Servicio

```bash
# Development logs
docker compose --profile development logs odoo-patco-dev
docker compose --profile development logs odoo-andessuyo-dev
docker compose --profile development logs db-dev
docker compose --profile development logs traefik

# Production logs
docker compose --profile production logs odoo-patco-prod
docker compose --profile production logs odoo-andessuyo-prod
docker compose --profile production logs db-prod

# Ver logs en tiempo real (follow)
docker compose --profile development logs -f odoo-patco-dev

# Ver últimas 100 líneas
docker compose --profile development logs --tail=100 odoo-patco-dev
```

### Acceder a Contenedores

```bash
# Development - Acceder a contenedor Odoo PATCO
docker compose exec odoo-patco-dev bash

# Development - Acceder a contenedor Odoo Andessuyo
docker compose exec odoo-andessuyo-dev bash

# Development - Acceder a PostgreSQL
docker compose exec db-dev bash

# Production - Acceder a contenedor Odoo PATCO
docker compose --profile production exec odoo-patco-prod bash

# Production - Acceder a contenedor Odoo Andessuyo
docker compose --profile production exec odoo-andessuyo-prod bash
```

### Verificar Configuración

```bash
# Development - Ver configuración Odoo
docker compose exec odoo-patco-dev cat /etc/odoo/odoo.conf

# Production - Ver configuración Odoo
docker compose --profile production exec odoo-patco-prod cat /etc/odoo/odoo.conf
```

---

## 🔧 Solución de Problemas Específicos

### WebSockets (Development)

```bash
# Linux - Ejecutar script de corrección
./scripts/fix-websockets.sh

# Verificar que Evented Service esté corriendo
docker exec odoo-patco-app tail -n 20 /var/log/odoo/odoo.log | grep "Evented Service"
# Salida esperada: Evented Service (longpolling) running on 0.0.0.0:8072

# Verificar OdooBot activo
docker exec odoo-patco-db psql -U odoo -d odoo_patco -c "SELECT u.id, p.name, u.active FROM res_users u JOIN res_partner p ON u.partner_id = p.id WHERE u.id = 1;"
# Salida esperada: 1 | OdooBot | t
```

### Actualización de Módulos

```bash
# Development - Actualizar TODOS los módulos
docker compose exec odoo-patco-dev /opt/odoo/odoo-bin -u all -d odoo_patco --stop-after-init

# Development - Actualizar módulo específico
docker compose exec odoo-patco-dev /opt/odoo/odoo-bin -d odoo_patco -u base --stop-after-init

# Production - Actualizar TODOS los módulos
docker compose --profile production exec odoo-patco-prod /opt/odoo/odoo-bin -u all -d odoo_patco --stop-after-init

# Production - Actualizar módulo específico
docker compose --profile production exec odoo-patco-prod /opt/odoo/odoo-bin -d odoo_patco -u base --stop-after-init
```

### Problemas de Puerto

```bash
# Si el puerto 8069 está ocupado, modificar docker-compose.yml
# Development: cambiar en el servicio odoo-patco-dev
ports:
  - "8070:8069"  # Usar puerto 8070 en lugar de 8069

# Production: cambiar en el servicio odoo-patco-prod
ports:
  - "8071:8069"  # Usar puerto 8071 en lugar de 8069
```

### Problemas de Permisos (Linux/Mac)

```bash
# Ajustar permisos de directorios
sudo chown -R 101:101 ./config
sudo chown -R 101:101 ./addons
sudo chown -R 101:101 ./extra-addons
```

---

## 📊 Referencia de Servicios

### Development - Servicios y Contenedores

| Servicio Compose | Contenedor Docker | Base de Datos | Descripción |
|------------------|-------------------|---------------|-------------|
| `traefik` | `patco-traefik-dev` | - | Proxy inverso y load balancer |
| `db-dev` | `odoo-patco-db` | `odoo_patco` | PostgreSQL 15 principal |
| `odoo-patco-dev` | `odoo-patco-app` | `odoo_patco` | Odoo Community 18 - PATCO |
| `odoo-andessuyo-dev` | `odoo-andessuyo-app` | `odoo_andessuyo` | Odoo Community 18 - Andessuyo |
| `db-init-andessuyo-dev` | Temporal | `odoo_andessuyo` | Inicialización DB Andessuyo |

### Production - Servicios y Contenedores

| Servicio Compose | Contenedor Docker | Base de Datos | Descripción |
|------------------|-------------------|---------------|-------------|
| `db-prod` | `odoo-db-prod` | `odoo_patco` | PostgreSQL 15 principal |
| `odoo-patco-prod` | `odoo-patco-app-prod` | `odoo_patco` | Odoo Community 18 - PATCO |
| `odoo-andessuyo-prod` | `odoo-andessuyo-app-prod` | `odoo_andessuyo` | Odoo Community 18 - Andessuyo |
| `odoo-patco-init-prod` | Temporal | `odoo_patco` | Inicialización DB PATCO |
| `odoo-andessuyo-init-prod` | Temporal | `odoo_andessuyo` | Inicialización DB Andessuyo |

### Volúmenes Principales

```bash
# Development
docker volume ls | grep -E "(dev|development)"
# odoo-patco-web-data-dev      # Datos web Odoo PATCO
docker volume ls | grep odoo
# odoo-andessuyo-web-data-dev  # Datos web Odoo Andessuyo
# odoo-patco-db-data-dev       # Datos PostgreSQL

# Production
docker volume ls | grep -E "(prod|production)"
# odoo-patco-web-data-prod     # Datos web Odoo PATCO
# odoo-andessuyo-web-data-prod # Datos web Odoo Andessuyo
# odoo-patco-db-data-prod      # Datos PostgreSQL
```

### Redes

```bash
# Development
docker network ls | grep dev
# odoo-network-dev             # Red bridge para development

# Production
docker network ls | grep prod
# odoo-patco-network-prod      # Red bridge para production
# web_gateway                  # Red external para Traefik
```

---

## ⚠️ Comandos de Emergencia (Último Recurso)

```bash
# ⚠️ CUIDADO: Elimina TODOS los contenedores, redes y volúmenes
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
docker network prune -f
docker volume prune -f
docker system prune -af
```

---

**Nota**: Esta guía está optimizada para el proyecto PATCO con Odoo Community 18. Para producción, considerar configuraciones adicionales de seguridad, SSL/TLS, y monitoreo.