# Guía Técnica General (KISS)

## Servicios Odoo
- Desarrollo: dos servicios Odoo detrás de Traefik.
  - `patco.local` → DB `odoo_patco`.
  - `andessuyo.local` → DB `odoo_andessuyo`.
- Producción: dominios reales detrás de Traefik.
  - `erp.patcoperu.com` y `erp.andessuyo.com`.
- Ambos usan el mismo servidor PostgreSQL.

## Bases de Datos y Auto-creación
- Bases: `odoo_patco` y `odoo_andessuyo`.
- Auto-creación `odoo_andessuyo`:
  - Servicios de init (`db-init-andessuyo-dev` y `db-init-andessuyo-prod`) verifican si la DB existe.
  - Si no existe, la crean (primera vez). Idempotente.
  - Aplica en perfiles `development` y `production`.

## Perfiles de Compose
- `development`: corre ambos Odoo; Traefik en `:80`.
- `production`: corre servicios con dominios reales; Traefik con TLS.

## Rutas y Acceso (contexto rápido)
- Desarrollo: `/home/chris/PAT02/`.
- Producción: `/opt/PAT02/` vía `ssh -i /home/chris/.ssh/id_rsa -p 22022 root@161.132.41.191` (IA: solo lectura).
- Cambios en producción: se entregan pasos para ejecución manual por el usuario.

## Notas útiles
- Compose define etiquetas Traefik para cada servicio y mapea websockets a `8072`.
- Use `documentation/guia-docker.md` y `guia-git.md` para operaciones específicas.