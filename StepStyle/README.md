# StepStyle

Tienda virtual académica con frontend HTML/CSS/JS, backend Python y base de datos PostgreSQL (Neon) en producción o SQLite en local.

## Inicio rápido

1. Instalar Python 3.10 o superior.
2. Configurar una cuenta administradora antes del primer arranque:

```bash
export STEPSTYLE_ADMIN_EMAIL=admin@stepstyle.test
export STEPSTYLE_ADMIN_PASSWORD='CAMBIAR_POR_CLAVE_SEGURA_123!'
python3 backend/server.py
```

En Windows PowerShell, utilizar `$env:STEPSTYLE_ADMIN_EMAIL=...` y `$env:STEPSTYLE_ADMIN_PASSWORD=...`.

3. Abrir `http://127.0.0.1:8000/` (no abrir el HTML directamente).
4. Registrar un cliente en `registro.html`, comprar con pago simulado y entrar como administrador en `admin.html`.

## Despliegue público (GitHub Pages + Render + Neon)

| Pieza | Servicio | Detalle |
|---|---|---|
| Frontend | GitHub Pages | `https://monicaalfaro09.github.io/StepStyle/StepStyle/` |
| Backend / API | Render (plan gratuito) | `render.yaml` en la raíz del repo, servicio `stepstyle-api` |
| Base de datos | Neon PostgreSQL | proyecto `stepstyle` |

1. **Neon:** crear el proyecto `stepstyle` y copiar la cadena de conexión (`postgresql://...?sslmode=require`).
2. **Render:** *New → Blueprint*, elegir este repositorio. Render lee `render.yaml` y pide:
   - `DATABASE_URL`: la cadena de Neon (solo aquí, **nunca** en el repositorio).
   - `STEPSTYLE_ADMIN_EMAIL` y `STEPSTYLE_ADMIN_PASSWORD` (12+ caracteres): cuenta admin inicial.
3. Al arrancar, el servidor aplica las migraciones de `backend/migrations/` y carga los 15 productos semilla.
4. Verificar `https://stepstyle-api-i381.onrender.com/api/health` → `{"ok": true, "db": "postgresql"}`.
5. Si Render asigna otra URL, cambiar `STEPSTYLE_REMOTE_API` en `js/api.js`.

El plan gratuito de Render suspende el servicio tras ~15 min sin uso; la primera petición puede tardar cerca de un minuto.

Sin `DATABASE_URL` el servidor usa SQLite local, como antes.

## Pruebas

```bash
python3 backend/tests/e2e_api.py http://127.0.0.1:8000 admin@stepstyle.test 'CLAVE_ADMIN' https://monicaalfaro09.github.io
```

Cubre compra completa, idempotencia, inventario insuficiente, cupón, cancelación con reposición de stock, devoluciones, panel admin, bloqueo de rutas admin, CORS y cierre de sesión.

## Respaldo y restauración (PostgreSQL)

```bash
pg_dump "$DATABASE_URL" -Fc -f backups/stepstyle_$(date +%F).dump
pg_restore --clean --if-exists -d "$DATABASE_URL" backups/stepstyle_AAAA-MM-DD.dump
```

Neon además permite restaurar a un punto en el tiempo desde su panel.

## Rutas principales

`GET /api/products`, `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/me`, `POST /api/orders`, `GET /api/orders`, `POST /api/returns`, `GET /api/returns`, `GET /api/admin/products`, `POST /api/admin/products`, `PATCH /api/admin/products/{sku}`, `GET /api/admin/orders`, `PATCH /api/admin/orders/{id}`, `GET /api/admin/returns`, `PATCH /api/admin/returns/{id}`, `GET /api/admin/reports`, `GET /api/admin/orders/{id}`, `GET /api/admin/inventory`, `GET /api/admin/audit`, `GET /api/health`.

Autenticación con token temporal (8 h) guardado como hash en la tabla `sessions`, por lo que sobrevive a reinicios; límite de intentos de login y registro por IP; contraseña derivada mediante PBKDF2-HMAC-SHA256. En local, la base se crea automáticamente en `backend/stepstyle.sqlite3`.

## Alcance

Pago simulado: nunca se envían datos de tarjeta al backend. No hay integración CFDI. Proyecto académico: no usar con datos personales ni pagos reales.
