# StepStyle

Tienda virtual académica con frontend HTML/CSS/JS, backend Python estándar y base de datos SQLite.

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

**No utilizar GitHub Pages para la tienda operativa:** solo publica archivos estáticos; no ejecuta este backend. La demo debe servirse desde el servidor Python. No publicar SQLite, contraseñas ni datos reales.

## Rutas principales

`GET /api/products`, `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/me`, `POST /api/orders`, `GET /api/orders`, `POST /api/returns`, `GET /api/returns`, `GET /api/admin/products`, `POST /api/admin/products`, `PATCH /api/admin/products/{sku}`, `GET /api/admin/orders`, `PATCH /api/admin/orders/{id}`, `GET /api/admin/returns`, `PATCH /api/admin/returns/{id}`, `GET /api/admin/reports`.

Autenticación con token temporal; contraseña derivada mediante PBKDF2-HMAC-SHA256. La base se crea automáticamente en `backend/stepstyle.sqlite3`. Para respaldar, detener el servidor y copiar el archivo SQLite a un lugar seguro.

## Alcance

Pago simulado: nunca se envían datos de tarjeta al backend. No hay integración CFDI. El sistema es una demostración local, no un despliegue de producción. Para exposición pública se requieren HTTPS, gestión persistente de sesiones, protección CSRF/CORS, rate limiting, monitoreo y auditoría de seguridad.
