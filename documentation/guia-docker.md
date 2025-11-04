# 🐳 Guía de Gestión Docker - Proyecto PATCO

## 📋 Resumen del Problema y Solución

### ❌ Problema Identificado
Cuando ejecutas `docker compose down`, algunos contenedores no se detienen porque:

1. **Servicios con perfiles específicos**: Los servicios con `profiles` (como `ai-setup`, `office-services`) no se incluyen en el comando básico `docker compose down`
2. **Contenedores huérfanos**: Contenedores que se ejecutaron con perfiles específicos quedan "huérfanos" y no se gestionan con comandos básicos
3. **Red en uso**: La red `odoo-patco-network` permanece activa mientras haya contenedores conectados a ella
4. **⚠️ NUEVO PROBLEMA**: Error "Resource is still in use" al intentar eliminar la red

### ✅ Solución Implementada
Para detener TODOS los servicios correctamente, debes usar comandos específicos según el perfil.

### 🔧 Solución para "Resource is still in use"
**Causa**: Contenedores individuales pueden quedar conectados a la red sin aparecer en `docker ps`, especialmente servicios IA que se ejecutan con perfiles específicos.

**Solución**: Usar `docker network inspect` para identificar contenedores conectados y eliminarlos manualmente antes de eliminar la red.

## Cuando quieras resetear completamente el entorno, usa esta secuencia:
```bash
# 1. Detener todos los perfiles
docker compose --profile ai-setup --profile office-services down -v

# 2. Si la red sigue en uso, inspeccionarla
docker network inspect odoo-patco-network

# 3. Eliminar contenedores conectados manualmente
docker stop [nombre-contenedor]
docker rm [nombre-contenedor]

# 4. Eliminar la red
docker network rm odoo-patco-network

# 5. Reiniciar desde cero
docker compose up -d
```
### Scripts de WebSockets

```powershell
# Windows - Corrección de problemas de websockets
.\scripts\fix-websockets.ps1

# Windows - Configuración preventiva
.\scripts\setup-websockets.ps1
```

```bash
# Linux - Corrección de problemas de websockets
./scripts/fix-websockets.sh
```

### Gestión de Datos

```bash
# Backup de la base de datos
docker compose exec db pg_dump -U odoo odoo_patco > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar base de datos
docker compose exec -T db psql -U odoo odoo_patco < backup_file.sql

# Acceder a la base de datos
docker compose exec db psql -U odoo -d odoo_patco
```

## 🚀 Comandos de Gestión por Perfiles

### 1. **Servicios Básicos** (Odoo + PostgreSQL)
```bash
# Reiniciar assets
docker exec odoo-patco-db psql -U odoo -d odoo_patco -c "DELETE FROM ir_attachment WHERE res_model = 'ir.ui.view' AND (name ILIKE '%.assets_%.css' OR name ILIKE '%.assets_%.js');"

# Iniciar servicios básicos
docker compose up -d

# Detener servicios básicos
docker compose down

# Detener y eliminar volúmenes
docker compose down -v
```

### 2. **Servicios IA de Configuración** (Perfil: ai-setup)
```bash
# Iniciar servicios de configuración IA
docker compose --profile ai-setup up -d

# Detener servicios de configuración IA
docker compose --profile ai-setup down

# Detener y eliminar volúmenes
docker compose --profile ai-setup down -v
```

### 3. **Servicios de Oficina** (Perfil: office-services)
```bash
# Iniciar OnlyOffice Document Server
docker compose --profile office-services up -d

# Detener OnlyOffice Document Server
docker compose --profile office-services down

# Detener y eliminar volúmenes
docker compose --profile office-services down -v
```

### 4. **TODOS los Servicios** (Comando Universal)
```bash
# Iniciar TODOS los servicios
docker compose --profile ai-setup --profile office-services up -d

# Detener TODOS los servicios
docker compose --profile ai-setup --profile office-services down

# Detener TODOS y eliminar volúmenes
docker compose --profile ai-setup --profile office-services down -v
```

---

## 🔧 Comandos de Limpieza Completa

### Método 1: Limpieza por Perfiles
```bash
# Detener todos los perfiles
docker compose --profile ai-setup --profile office-services down -v

# Verificar que no queden contenedores
docker ps -a

# Limpiar contenedores huérfanos
docker container prune -f
```

### Método 2: Limpieza Manual (Método Usado)
```bash
# 1. Identificar contenedores activos
docker ps -a

# 2. Detener contenedores específicos
docker stop patco-document-indexer patco-mcp-server patco-onlyoffice-documentserver patco-onlyoffice-rabbitmq

# 3. Eliminar contenedores
docker rm patco-document-indexer patco-mcp-server patco-onlyoffice-documentserver patco-onlyoffice-rabbitmq

# 4. Eliminar red
docker network rm odoo-patco-network

# 5. Limpiar recursos no utilizados
docker system prune -f
```

### Método 2.1: Solución para Red "Resource is still in use"
```bash
# ⚠️ PROBLEMA: La red odoo-patco-network no se elimina con "Resource is still in use"
# ✅ SOLUCIÓN: Identificar y eliminar contenedores conectados manualmente

# 1. Inspeccionar qué contenedores están usando la red
docker network inspect odoo-patco-network

# 2. Identificar contenedores en la sección "Containers" del output
# Ejemplo: "patco-document-indexer" aparece conectado

# 3. Detener el contenedor específico
docker stop patco-document-indexer

# 4. Eliminar el contenedor
docker rm patco-document-indexer

# 5. Ahora eliminar la red
docker network rm odoo-patco-network

# 6. Verificar que la red fue eliminada
docker network ls | grep odoo-patco
```

### Método 3: Limpieza Nuclear (Último Recurso)
```bash
# ⚠️ CUIDADO: Esto elimina TODOS los contenedores y redes
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
docker network prune -f
docker volume prune -f
docker system prune -af
```

---

## 📊 Servicios del Proyecto PATCO

### Servicios Básicos (Sin perfil)
- `db` → `odoo-patco-db` (PostgreSQL 15)
- `odoo` → `odoo-patco-app` (Odoo Community 18)

### Servicios IA - Configuración (Perfil: ai-setup)
- `pgvector-setup` → `patco-pgvector-setup`
- `ai-services-validator` → `patco-ai-validator`

### Servicios IA - Producción (Sin perfil específico)
- `document-indexer` → `patco-document-indexer`
- `mcp-server` → `patco-mcp-server`
- `langgraph-server` → `patco-langgraph-server`

### Servicios de Oficina (Perfil: office-services)
- `onlyoffice-documentserver` → `patco-onlyoffice-documentserver`
- `onlyoffice-rabbitmq` → `patco-onlyoffice-rabbitmq`

---

## 🌐 Gestión de Redes

### Red Principal
- **Nombre**: `odoo-patco-network`
- **Tipo**: Bridge
- **Propósito**: Comunicación entre todos los servicios PATCO

### Verificar Estado de Red
```bash
# Listar redes
docker network ls

# Inspeccionar red específica
docker network inspect odoo-patco-network

# Ver qué contenedores están conectados
docker network inspect odoo-patco-network | grep -A 10 "Containers"
```

---

## 📦 Gestión de Volúmenes

### Volúmenes del Proyecto
```bash
# Listar volúmenes PATCO
docker volume ls | grep patco

# Volúmenes principales:
# - odoo-patco-web-data (datos web Odoo)
# - odoo-patco-db-data (base de datos PostgreSQL)
# - patco-onlyoffice-* (datos OnlyOffice)
```

### Limpieza de Volúmenes
```bash
# Eliminar volúmenes específicos
docker volume rm odoo-patco-web-data odoo-patco-db-data

# Eliminar todos los volúmenes no utilizados
docker volume prune -f
```

---

## 🚨 Comandos de Emergencia

### Verificar Estado General
```bash
# Ver todos los contenedores
docker ps -a

# Ver uso de recursos
docker stats

# Ver logs de un servicio específico
docker compose logs odoo
docker compose logs db
```

### Reinicio Completo del Proyecto
```bash
# 1. Detener todo
docker compose --profile ai-setup --profile office-services down -v

# 2. Limpiar contenedores huérfanos
docker container prune -f

# 3. Limpiar redes no utilizadas
docker network prune -f

# 4. Iniciar servicios básicos
docker compose up -d

# 5. Iniciar servicios adicionales si es necesario
docker compose --profile office-services up -d
```

---
## Solución de Problemas

### Problemas Comunes

1. **Puerto 8069 ocupado**:
   ```bash
   # Cambiar puerto en docker-compose.yml
   ports:
     - "8070:8069"  # Usar puerto 8070
   ```

2. **Error de conexión a base de datos**:
   ```bash
   # Verificar que PostgreSQL esté ejecutándose
   docker compose logs db
   
   # Reiniciar servicios
   docker compose down && docker compose up -d
   ```

3. **Problemas de permisos**:
   ```bash
   # En Linux/Mac, ajustar permisos
   sudo chown -R 101:101 ./config
   sudo chown -R 101:101 ./addons
   ```

4. **Problemas de WebSockets (SOLUCIONADO AUTOMÁTICAMENTE)**:
   ```powershell
   # Windows - Ejecutar script de corrección
   .\scripts\fix-websockets.ps1
   ```
   ```bash
   # Linux - Ejecutar script de corrección
   ./scripts/fix-websockets.sh
   ```

5. **Problema de assets corruptos (CSS)**:
   ```bash
   # 1. Limpiar assets corruptos
   docker compose exec db psql -U odoo -d odoo_patco -c "DELETE FROM ir_attachment WHERE res_model = 'ir.ui.view' AND (name ILIKE '%.assets_%.css' OR name ILIKE '%.assets_%.js');"

   # 2. Reiniciar Odoo
   docker compose restart odoo
   ```

6. **Actualizaciones de los módulos, si hay cambios**:
   ```bash
   # Actualizar módulos
   docker compose exec odoo odoo-bin -u all -d odoo-patco
   
   # o esto para un solo módulo 
   docker compose exec odoo ./odoo-bin -d nombre_de_tu_db -u base --stop-after-init
   ```


### Logs y Diagnóstico

```bash
# Ver logs detallados
docker compose logs --tail=100 -f

# Acceder al contenedor de Odoo
docker compose exec odoo bash

# Verificar configuración
docker compose exec odoo cat /etc/odoo/odoo.conf

# Ver logs específicos de websockets
Get-Content logs/odoo.log | Select-String -Pattern "websocket|longpolling|Evented"
```

### Verificación de WebSockets

```bash
# Verificar que el Evented Service esté corriendo
docker exec odoo-patco-app tail -n 20 /var/log/odoo/odoo.log | grep "Evented Service"

# Salida esperada:
# Evented Service (longpolling) running on 0.0.0.0:8072
```

```sql
# Verificar que OdooBot esté activo
docker exec odoo-patco-db psql -U odoo -d odoo_patco -c "SELECT u.id, p.name, u.active FROM res_users u JOIN res_partner p ON u.partner_id = p.id WHERE u.id = 1;"

# Salida esperada:
# 1 | OdooBot | t
```

**Nota**: Este es un sistema en desarrollo. Para producción, considerar configuraciones adicionales de seguridad, SSL/TLS, y monitoreo.