# Manual de usuario — administrador

## Acceso
1. Iniciar el servidor.
2. Abrir `login.html`.
3. Ingresar con la cuenta definida en `.env` como `ADMIN_EMAIL` y `ADMIN_PASSWORD`.
4. Abrir `admin.html`.

## Módulos
- **Resumen:** cantidad de productos, pedidos, ventas registradas y alertas de stock bajo.
- **Productos e inventario:** crear productos, ajustar existencia, actualizar datos básicos y dar de baja lógica.
- **Pedidos:** consultar folio, cliente, correo, estado y total; actualizar estado a pagado, preparando, enviado, entregado, cancelado o reembolsado.
- **Devoluciones:** consultar solicitudes, actualizar estado y escribir resolución.
- **Bitácora:** revisar operaciones administrativas recientes.

## Reglas operativas
- Ajustar inventario solo con motivo documentado.
- Verificar el pedido antes de cambiar su estado.
- La cancelación desde el panel restaura las unidades y registra el movimiento de entrada.
- Una devolución registrada no implica reembolso automático; el responsable debe revisar el caso y registrar la resolución.
- Cerrar sesión al terminar.
