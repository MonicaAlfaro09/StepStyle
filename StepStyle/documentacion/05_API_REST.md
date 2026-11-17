# Documento de API REST

Todas las rutas se sirven desde el mismo origen. Las rutas protegidas usan sesión cookie. Los datos de prueba no deben ser reales.

| Método | Ruta | Acceso | Función |
|---|---|---|---|
| GET | `/api/health` | Público | Estado del servicio |
| POST | `/api/auth/register` | Público | Registrar comprador |
| POST | `/api/auth/login` | Público | Iniciar sesión |
| POST | `/api/auth/logout` | Sesión | Cerrar sesión |
| GET | `/api/auth/me` | Público | Consultar sesión actual |
| GET | `/api/products` | Público | Catálogo activo |
| GET | `/api/products/:id` | Público | Detalle de producto |
| POST | `/api/orders` | Cliente | Crear pedido y descontar stock |
| GET | `/api/orders/mine` | Cliente | Pedidos propios |
| GET | `/api/orders/:id` | Dueño/Admin | Detalle de pedido |
| GET | `/api/returns/mine` | Cliente | Solicitudes propias |\n| POST | `/api/returns` | Cliente | Crear solicitud de devolución |
| GET | `/api/admin/summary` | Admin | Indicadores |
| GET/POST | `/api/admin/products` | Admin | Listar/crear productos |
| PATCH/DELETE | `/api/admin/products/:id` | Admin | Actualizar/baja lógica |
| GET | `/api/admin/orders` | Admin | Listar pedidos |
| PATCH | `/api/admin/orders/:id` | Admin | Cambiar estado |
| GET | `/api/admin/returns` | Admin | Listar devoluciones |
| PATCH | `/api/admin/returns/:id` | Admin | Resolver/actualizar solicitud |
| GET | `/api/admin/audit` | Admin | Bitácora |

## Ejemplo de creación de pedido
`POST /api/orders` con sesión iniciada:
```json
{
  "items":[{"id":"ST001","size":"27","color":"Blanco","quantity":1}],
  "customer":{"name":"Cliente Demo","email":"cliente@example.test","address":"Calle de prueba 10","city":"Ciudad Victoria","state":"Tamaulipas","zip":"87000","phone":"8340000000"},
  "paymentMethod":"Simulación aprobada",
  "acceptedTerms":true
}
```
El servidor consulta el catálogo y calcula precio, IVA y envío; no acepta importes enviados por el navegador. Respuesta esperada: HTTP 201 y un objeto `order` con `number`, `total` y `status`.

## Códigos
- 200 operación correcta.
- 201 recurso creado.
- 400 datos o reglas no válidos.
- 401 sesión requerida.
- 403 rol insuficiente.
- 404 recurso inexistente.
- 409 conflicto, duplicado o stock insuficiente.
- 500 error interno no esperado.

## Seguridad
Consultas SQL parametrizadas, contraseñas con bcrypt, sesiones HttpOnly/SameSite, limitación de solicitudes y autorización por rol. Para producción se requiere HTTPS, secreto robusto, política CSRF formal, CSP ajustada, monitoreo y pruebas independientes.
