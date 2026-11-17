# Plan y reporte de pruebas

Completar la columna de resultado obtenido y adjuntar capturas/consultas reales durante la ejecución. No marcar como aprobado sin ejecutar la prueba.

| ID | Caso | Pasos resumidos | Resultado esperado | Resultado obtenido |
|---|---|---|---|---|
| P01 | Catálogo | Abrir inicio y buscar “Nike” | Lista filtrada | Pendiente de ejecución |
| P02 | Filtro | Elegir categoría y género | Coincidencias correctas | Pendiente |
| P03 | Carrito | Agregar, cambiar cantidad y eliminar | Subtotal actualizado | Pendiente |
| P04 | Registro | Crear cliente con correo nuevo | Cuenta creada | Pendiente |
| P05 | Login incorrecto | Contraseña incorrecta | HTTP 401 | Pendiente |
| P06 | Checkout | Completar dirección, aceptar términos y confirmar | Folio generado | Pendiente |
| P07 | Stock insuficiente | Solicitar cantidad mayor a existencia vía API | HTTP 409, sin stock negativo | Pendiente |
| P08 | Inventario | Confirmar pedido | Stock disminuye y movimiento salida | Pendiente |
| P09 | Admin no autorizado | Acceder a `/api/admin/orders` como cliente | HTTP 403 | Pendiente |
| P10 | Admin autorizado | Acceder con rol admin | Pedidos visibles | Pendiente |
| P11 | Estado pedido | Cambiar a enviado | Estado actualizado | Pendiente |
| P12 | Cancelación | Cancelar pedido no cancelado | Stock restaurado y movimiento entrada | Pendiente |
| P13 | Devolución | Registrar solicitud | Folio de solicitud y estado recibida | Pendiente |
| P14 | XSS/SQLi básico | Enviar cadenas de prueba en campos de texto | No ejecutar ni alterar consultas | Pendiente |
| P15 | Respaldo | Copiar DB, restaurar y verificar | Datos consistentes | Pendiente |
| P16 | Responsive | Probar 360 px, tableta y escritorio | Sin desbordamientos críticos | Pendiente |
| P17 | Accesibilidad | Teclado, foco, etiquetas y contraste | Registrar hallazgos | Pendiente |

## Formato de evidencia
Para cada prueba, anexar: fecha, navegador, ambiente, usuario/rol, datos de prueba, captura, respuesta HTTP o consulta SQL, resultado real y observaciones. Esta plantilla no representa pruebas ya ejecutadas.
