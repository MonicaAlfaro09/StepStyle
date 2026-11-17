# Entrega StepStyle — Proyecto integrador

Esta carpeta contiene el frontend original ampliado, un backend Express, una base SQLite, un panel administrativo, políticas académicas y manuales.

## Importante antes de entregar
- **No es suficiente subir el ZIP a GitHub Pages.** GitHub Pages solo publica archivos estáticos y no ejecuta `server.js`, sesiones ni SQLite. Para demostrar la versión completa, ejecutar en un equipo con Node.js o desplegar el backend en un hosting que admita Node y almacenamiento persistente.
- Los pedidos, cuentas, inventario y solicitudes se guardan en SQLite cuando se ejecuta el servidor.
- Los pagos son simulados. No se capturan tarjetas ni CVV.
- StepStyle es un proyecto académico. Los datos de proveedor/contacto son ficticios o pendientes y los documentos legales son modelos para revisión, no asesoría jurídica.
- No subir `.env`, `node_modules/` ni la base SQLite con datos personales a GitHub.

## Inicio rápido
1. Instala Node.js 20 o superior.
2. Descomprime la carpeta completa.
3. Copia `.env.example` como `.env`.
4. Cambia `SESSION_SECRET`, `ADMIN_PASSWORD` y `ADMIN_EMAIL` por valores privados.
5. Abre una terminal en la carpeta del proyecto y ejecuta `npm install`.
6. Ejecuta `npm start`.
7. Abre `http://localhost:3000`.
8. Comprueba `http://localhost:3000/api/health`.

## Cuenta administrativa inicial
Se crea al iniciar la base por primera vez, usando `ADMIN_EMAIL` y `ADMIN_PASSWORD` del `.env`. En el `.env.example` hay valores ilustrativos; **cámbialos antes de ejecutar**. La cuenta demo por defecto solo sirve para pruebas locales si no cambiaste las variables.

## Prueba principal
1. Registra un cliente desde Registro.
2. Inicia sesión, agrega un producto y abre el carrito.
3. Completa la dirección, selecciona pago simulado y acepta términos.
4. Confirma el pedido.
5. Cierra sesión e inicia con el administrador.
6. Abre `admin.html`, revisa pedidos e inventario.
7. Solicita una devolución desde `devoluciones.html` con la cuenta cliente y revisa la solicitud en el panel.

## Estructura
- `index.html`, `producto.html`, `carrito.html`, `checkout.html`: tienda.
- `registro.html`, `login.html`, `perfil.html`: cuentas.
- `admin.html`: administración protegida por rol.
- `devoluciones.html`, `legal.html`: atención y políticas.
- `server.js`: API, sesiones y reglas de negocio.
- `database/schema.sql`: esquema SQLite.
- `data_products.json`: catálogo semilla de 15 productos.
- `documentacion/`: manuales, arquitectura, pruebas y matriz de requisitos.
