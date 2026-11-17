# StepStyle — Tienda virtual académica

Tienda responsive de calzado con frontend HTML/CSS/JavaScript, backend Node.js/Express, API REST, autenticación por sesión y base SQLite.

## Funcionalidades
### Comprador
- Catálogo inicial de 15 productos, búsqueda, filtros y ordenamiento.
- Ficha de producto, talla, color y stock.
- Favoritos y carrito en navegador.
- Registro e inicio de sesión con backend y hash bcrypt.
- Checkout de varios pasos, dirección, cálculo de envío, IVA y aceptación de términos.
- Pago simulado sin capturar tarjeta ni CVV.
- Pedido persistido en SQLite con folio y partidas históricas.
- Validación de stock y precios en servidor; descuento transaccional de inventario.
- Perfil, historial y solicitud de devolución.

### Administrador
- Dashboard con conteos y ventas registradas.
- Alta, edición básica, baja lógica y ajuste de stock.
- Consulta y actualización de pedidos.
- Gestión de solicitudes de devolución.
- Bitácora de operaciones.
- Endpoints administrativos protegidos por rol.

### Seguridad implementada y límites
- Hash bcrypt para contraseñas.
- Sesión de servidor con cookie HttpOnly/SameSite.
- Rate limiting general y de autenticación.
- Helmet y consultas SQL parametrizadas.
- Validación de rol en endpoints administrativos.
- No se reciben datos de tarjeta.
- Para producción faltan revisión de CSRF, CSP estricta, HTTPS real, gestión de secretos, pruebas de penetración, correo de recuperación, monitoreo y revisión jurídica.

## Instalación
Requisitos: Node.js 20 o superior.

```bash
npm install
```
Copia `.env.example` a `.env`, cambia el secreto de sesión y la contraseña administrativa, después:

```bash
npm start
```
Abre `http://localhost:3000`. Verifica `http://localhost:3000/api/health`.

La base `data/stepstyle.sqlite` y las tablas se crean automáticamente en el primer inicio.

## Cuenta administrativa
La cuenta inicial se define con `ADMIN_EMAIL` y `ADMIN_PASSWORD` en `.env`. El ejemplo de `.env.example` contiene valores ilustrativos; reemplázalos antes de ejecutar y nunca publiques tu `.env`.

## Estructura
- HTML: `index.html`, `producto.html`, `carrito.html`, `checkout.html`, `confirmacion.html`, `registro.html`, `login.html`, `perfil.html`, `favoritos.html`, `admin.html`, `legal.html`, `devoluciones.html`.
- `js/`: lógica del navegador.
- `server.js`: backend y API.
- `database/schema.sql`: esquema relacional.
- `data_products.json`: catálogo inicial.
- `documentacion/`: manuales, ficha técnica, API, modelo de datos, matriz legal y pruebas.

## Publicación
GitHub Pages solo aloja frontend estático y **no ejecuta Express ni SQLite**. Para cumplir la demostración de backend, publicar la aplicación en un hosting Node.js con almacenamiento persistente y HTTPS. No desplegar la base de datos en un hosting efímero.

## Alcance académico
StepStyle no procesa pagos reales, no despacha productos, no emite CFDI y utiliza proveedor/datos de contacto simulados. Las políticas legales son borradores informativos y requieren validación antes de cualquier actividad comercial.
