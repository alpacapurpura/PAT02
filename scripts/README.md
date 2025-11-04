# Scripts de WebSockets - PATCO Suite

Esta carpeta contiene scripts automatizados para resolver y prevenir problemas de websockets en Odoo 18.

## 📋 Scripts Disponibles

### 1. `fix-websockets.ps1` (Windows)
**Propósito:** Corrige problemas de websockets cuando ya han ocurrido.

**Uso:**
```powershell
.\scripts\fix-websockets.ps1
```

**Acciones que realiza:**
- ✅ Activa OdooBot (usuario ID: 1)
- 🧹 Elimina assets corruptos de websockets
- 📁 Limpia archivos físicos corruptos del filestore
- 🔄 Reinicia Odoo para regenerar assets
- 🔍 Verifica que el Evented Service esté corriendo
- 🧽 Limpia logs para pruebas

### 2. `fix-websockets.sh` (Linux/Producción)
**Propósito:** Versión para Linux del script de corrección.

**Uso:**
```bash
./scripts/fix-websockets.sh
```

**Nota:** Mismo comportamiento que la versión de Windows.

### 3. `setup-websockets.ps1` (Windows)
**Propósito:** Configuración preventiva después de `docker compose up -d`.

**Uso:**
```powershell
.\scripts\setup-websockets.ps1
```

**Acciones preventivas:**
- 🔧 Configura OdooBot como activo desde el inicio
- 🧹 Limpia assets potencialmente problemáticos
- 🔍 Verifica configuración de workers
- 🌐 Verifica que Traefik esté corriendo

## 🚀 Flujo Recomendado

### Para Desarrollo Local (Windows)

1. **Instalación limpia:**
```powershell
docker compose down -v
docker compose up -d
.\scripts\setup-websockets.ps1
```

2. **Si hay problemas de websockets:**
```powershell
.\scripts\fix-websockets.ps1
```

### Para Producción (Linux)

1. **Instalación limpia:**
```bash
docker compose down -v
docker compose up -d
# Esperar 60 segundos
./scripts/fix-websockets.sh
```

2. **Si hay problemas de websockets:**
```bash
./scripts/fix-websockets.sh
```

## 🔍 Síntomas de Problemas de WebSockets

- ❌ Mensaje "Se perdió la conexión en tiempo real..."
- 🔄 Necesidad de recargar la página para ver respuestas de OdooBot
- 📝 Mensajes no aparecen automáticamente en el chat
- 🚫 Error `KeyError: 'socket'` en logs
- 📦 Error `FileNotFoundError` para websocket_worker_bundle

## 📊 Verificación Manual

### Verificar Evented Service:
```bash
docker exec odoo-patco-app tail -n 20 /var/log/odoo/odoo.log | grep "Evented Service"
```

**Salida esperada:**
```
Evented Service (longpolling) running on 0.0.0.0:8072
```

### Verificar OdooBot:
```sql
docker exec odoo-patco-db psql -U odoo -d odoo_patco -c "SELECT u.id, p.name, u.active FROM res_users u JOIN res_partner p ON u.partner_id = p.id WHERE u.id = 1;"
```

**Salida esperada:**
```
 id |  name   | active 
----+---------+--------
  1 | OdooBot | t
```

### Verificar Assets:
```bash
docker exec odoo-patco-db psql -U odoo -d odoo_patco -c "SELECT COUNT(*) FROM ir_attachment WHERE name LIKE '%websocket_worker_bundle%';"
```

## 🛠️ Troubleshooting

### Error: "Contenedores no están corriendo"
```powershell
docker compose up -d
# Esperar 30 segundos
.\scripts\fix-websockets.ps1
```

### Error: "Base de datos no está lista"
```powershell
# Esperar más tiempo
Start-Sleep -Seconds 60
.\scripts\setup-websockets.ps1
```

### Websockets siguen sin funcionar
1. Verificar configuración de Traefik
2. Revisar logs: `Get-Content logs/odoo.log | Select-Object -Last 50`
3. Verificar puertos: `docker ps --format "table {{.Names}}\t{{.Ports}}"`

## 📝 Notas Importantes

- **Orden de ejecución:** Siempre ejecutar después de `docker compose up -d`
- **Tiempo de espera:** Los scripts incluyen esperas apropiadas
- **Logs limpios:** Los scripts limpian logs automáticamente
- **Idempotencia:** Los scripts se pueden ejecutar múltiples veces sin problemas
- **Compatibilidad:** Scripts probados con Odoo 18 Community + Traefik

## 🔗 URLs de Verificación

- **Odoo:** http://localhost (desarrollo) / tu-dominio.com (producción)
- **Traefik Dashboard:** http://localhost:8080 (desarrollo)
- **WebSocket Test:** Usar el chat interno de Odoo con OdooBot