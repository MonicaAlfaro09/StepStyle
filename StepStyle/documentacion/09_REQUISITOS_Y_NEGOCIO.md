# Propuesta de negocio y requisitos

## Descripción
StepStyle es una tienda académica ficticia de calzado moderno para hombres y mujeres. Su propuesta es facilitar la exploración de modelos casuales, deportivos y urbanos mediante un catálogo digital organizado por categoría, género y precio.

## Modelo
- Tipo: B2C (empresa a consumidor), simulado.
- Productos: tenis, zapatos, botines y otras categorías disponibles en el catálogo.
- Ingresos: margen sobre precio de venta; no se registran ingresos reales.
- Entrega: costos estimados de demostración; no existe logística real.
- Atención: canales simulados que deben sustituirse por datos de contacto reales si el proyecto se convierte en negocio.

## Misión, visión y valores propuestos
**Misión:** ofrecer una experiencia digital sencilla para descubrir calzado que combine estilo, comodidad y funcionalidad.
**Visión:** consolidar una propuesta de tienda virtual reconocible por su navegación clara y catálogo accesible.
**Valores:** transparencia, comodidad, confianza, inclusión y mejora continua.

## Segmento y buyer persona propuesto
Personas jóvenes y adultas que compran calzado casual o deportivo por internet, comparan precio/modelo y valoran fotografías, tallas y disponibilidad. Buyer persona de ejemplo: “Alex, 22 años, estudiante, consulta tiendas desde celular y compara precio, estilo y disponibilidad antes de comprar”. Es un arquetipo hipotético, no investigación de mercado.

## Competidores a investigar
Completar con evidencia fechada de al menos tres comercios comparables (por ejemplo, tiendas oficiales de marcas o retailers nacionales). Comparar navegación, precios de productos equivalentes, diferenciadores, entrega, cambios y garantías. No se inventan resultados ni precios en este documento.

## Requisitos funcionales
- RF01: mostrar catálogo de productos.
- RF02: buscar y filtrar productos.
- RF03: consultar detalle, talla, precio y existencia.
- RF04: administrar carrito.
- RF05: registrar e iniciar sesión.
- RF06: crear pedido de prueba con dirección y aceptación de términos.
- RF07: validar precio y stock en servidor.
- RF08: registrar pedidos y partidas.
- RF09: descontar inventario y registrar movimiento.
- RF10: consultar pedidos propios.
- RF11: restringir administración al rol admin.
- RF12: administrar productos, pedidos y solicitudes.
- RF13: registrar solicitudes de devolución.

## Requisitos no funcionales
- RNF01: interfaz adaptable a móvil y escritorio.
- RNF02: consultas parametrizadas.
- RNF03: contraseñas con bcrypt.
- RNF04: sesión con cookie HttpOnly y SameSite.
- RNF05: variables sensibles fuera del repositorio.
- RNF06: documentación de instalación y respaldo.
- RNF07: mensajes de error comprensibles.

## Reglas de negocio
- El servidor consulta precio y existencia del catálogo.
- No se permite stock negativo.
- El pedido se crea y el stock se descuenta en una transacción.
- El total se calcula en servidor.
- Se registra aceptación de términos y su versión.
- El administrador es el único que accede a endpoints administrativos.
- Cancelar un pedido restaura existencias y genera movimiento de inventario.

## Historias de usuario
- Como visitante quiero buscar por categoría para encontrar modelos.
- Como comprador quiero guardar productos en carrito para preparar una compra.
- Como comprador quiero confirmar un pedido de prueba y recibir un folio.
- Como administrador quiero actualizar existencias para reflejar disponibilidad.
- Como administrador quiero cambiar el estado del pedido para dar seguimiento.
- Como comprador quiero solicitar devolución y consultar su estado.
