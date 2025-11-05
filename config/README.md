# Odoo config (production security)

This folder contains the Odoo configuration used by containers via `- ./config:/etc/odoo` in `docker-compose.yml`.

## Security settings in `odoo.conf`

- `admin_passwd`: protects the Database Manager actions (create, backup, restore, drop). A strong randomly generated password is set. Rotate if compromised.
- `list_db = False`: hides database selector and prevents DB enumeration or creation from UI.
- `dbfilter = ^odoo_(patco|andessuyo)$`: restricts accessible DBs to the two production databases. Update this regex if adding new prod DBs.
- `proxy_mode = True`: required behind Traefik / TLS to trust `X-Forwarded-*` headers.

## Deployment notes

- The config is shared by both prod Odoo services (Patco and Andessuyo) through the mapped volume. Default DB per service is selected by container command (`-d odoo_patco` or `-d odoo_andessuyo`).
- After changes, review logs with `docker compose logs odoo-patco-prod odoo-andessuyo-prod | tail -n 200` and ensure Odoo starts without warnings.
- Never commit the `admin_passwd` elsewhere; it lives only in `config/odoo.conf`.

## Validation

- Access `https://erp.patcoperu.com` and `https://erp.andessuyo.com` should no longer show the public DB manager; direct login pages should load.
- The path `/web/database/selector` should return 404 or redirect when `list_db=False` is active.
