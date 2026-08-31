# StepStyle - Tienda virtual FrontEnd

Proyecto académico completo desarrollado con HTML5, CSS3 y JavaScript puro.

## Funciones implementadas
- Homepage responsive Mobile First.
- Catálogo con 15 productos y fotografías reales enlazadas desde Nike, adidas y PUMA.
- Búsqueda predictiva en tiempo real.
- Filtros combinados por categoría, género y precio.
- Ordenamiento por popularidad y precio.
- Ofertas con precio original tachado y porcentaje.
- Quick View en modal.
- Página de detalle de producto con talla, color, cantidad, stock, descripción y especificaciones.
- Wishlist persistente con LocalStorage.
- Carrito persistente con LocalStorage y control de cantidades/stock.
- Registro de usuarios con validación y medidor de fortaleza de contraseña.
- Login simulado contra usuarios guardados en LocalStorage.
- Sesión persistente y perfil.
- Checkout protegido: si no existe sesión, redirige al login.
- Checkout multistep: dirección, método de pago y revisión.
- Métodos simulados: tarjeta, transferencia y PayPal.
- Validación visual de formularios.
- Calculadora de envío por código postal.
- Cupones PROFE100 y STEP20.
- IVA 16%, descuento, envío y total en tiempo real.
- Simulación de pago con spinner de 2 segundos.
- Confirmación con orden aleatoria tipo ORD84920.
- Vaciado automático del carrito después de pagar.

## Usuario de prueba
- Correo: monica@stepstyle.mx
- Contraseña: StepStyle2026!

El usuario se crea automáticamente la primera vez que se abre `login.html`.

## Cupones
- `PROFE100`: $100 MXN de descuento.
- `STEP20`: 20% de descuento.

## Cálculo de envío
- Compra >= $2,500: gratis.
- CP 88000-88999: $99.
- CP 64000-64999 y 44000-44999: $129.
- Otros CP válidos: $169.

## Ejecutar
Se recomienda abrir la carpeta con VS Code y usar **Live Server** sobre `index.html`.

## Estructura
- `index.html`: inicio y catálogo.
- `producto.html`: detalle de producto.
- `carrito.html`: carrito.
- `favoritos.html`: wishlist.
- `registro.html`: alta de usuario.
- `login.html`: autenticación.
- `perfil.html`: sesión y pedidos.
- `checkout.html`: proceso de compra.
- `confirmacion.html`: Thank You Page.
- `js/common.js`: almacenamiento, sesión, carrito y layout común.

## Nota
Es un proyecto exclusivamente FrontEnd. No procesa pagos reales ni envía información a un servidor. Los datos se almacenan localmente en el navegador mediante LocalStorage.

## Publicar en GitHub Pages
El proyecto incluye `.github/workflows/pages.yml` para desplegar el sitio estático automáticamente desde la rama `main`.

Después de subir el proyecto a un repositorio público:
1. Abre **Settings > Pages**.
2. En **Build and deployment**, selecciona **GitHub Actions**.
3. Haz un push a `main` o ejecuta manualmente el workflow **Deploy StepStyle to GitHub Pages**.
