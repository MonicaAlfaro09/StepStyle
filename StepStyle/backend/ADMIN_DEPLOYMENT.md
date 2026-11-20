# Activación del panel de administración

El panel `admin.html` utiliza autenticación contra el backend. La autorización no depende de ocultar la página: los endpoints `/api/admin/*` verifican la sesión y el rol `admin` en el servidor.

## Variables de entorno en Render

En el servicio del backend, abre **Environment** y configura:

- `STEPSTYLE_ADMIN_EMAIL`: el correo de administrador indicado por la propietaria del proyecto.
- `STEPSTYLE_ADMIN_PASSWORD`: la contraseña de administrador indicada por la propietaria del proyecto (el backend exige al menos 12 caracteres).

Guarda los cambios y realiza un redeploy/reinicio del servicio. Al iniciar, el backend sincroniza el correo y el hash de contraseña del primer usuario administrador existente, o crea uno si todavía no existe. La contraseña no debe escribirse en archivos HTML, JavaScript ni en el repositorio.

## Publicación de productos

El formulario de `admin.html` envía el producto al endpoint autenticado `POST /api/admin/products`. La API guarda sus datos y metadatos en la base de datos. El catálogo público `GET /api/products` devuelve los productos activos; `js/api.js` actualiza el catálogo de la página principal con esos registros.

Para que esto funcione en el sitio publicado, despliega también los cambios de `backend/server.py` en Render y los archivos estáticos del proyecto en GitHub Pages. No publiques el backend ni credenciales dentro de GitHub Pages.

## Datos reales

El resumen, pedidos, devoluciones, inventario y auditoría muestran los registros existentes en la base de datos. Si la base de datos está vacía, se mostrarán conteos en cero y mensajes de que todavía no hay registros; no se generan pedidos o ventas ficticios.
