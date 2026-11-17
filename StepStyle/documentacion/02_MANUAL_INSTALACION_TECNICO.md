# Manual de instalación y técnico

## Requisitos
- Windows 10/11, macOS o Linux.
- Node.js 20 o superior y npm.
- Navegador actualizado.
- Permisos de escritura en la carpeta `data/`.

## Instalación
1. Descomprimir el proyecto.
2. Abrir terminal en la carpeta raíz (donde está `package.json`).
3. Ejecutar `npm install`.
4. Copiar `.env.example` a `.env`.
5. Configurar un secreto de sesión largo y aleatorio y una contraseña administrativa propia.
6. Ejecutar `npm start`.
7. Abrir `http://localhost:3000`.

La primera ejecución crea las tablas SQLite y carga los 15 productos desde `data_products.json`. También crea el administrador inicial si no existe uno. No se necesita ejecutar manualmente `database/schema.sql` porque `server.js` crea el esquema.

## Verificación
- `GET /api/health` debe responder `{"status":"ok","service":"StepStyle API","database":"connected"}`.
- La página de inicio debe mostrar el catálogo.
- Registrar una cuenta de cliente y revisar que se pueda iniciar sesión.
- Crear un pedido de prueba y revisar el panel admin.

## Variables de entorno
| Variable | Uso |
|---|---|
| PORT | Puerto HTTP, predeterminado 3000 |
| NODE_ENV | En producción activa cookie Secure |
| SESSION_SECRET | Secreto de firma de sesión; obligatorio cambiarlo |
| ADMIN_EMAIL | Correo de administrador inicial |
| ADMIN_PASSWORD | Contraseña de administrador inicial |
| DB_FILE | Ruta de archivo SQLite |

## Estructura de carpetas
`css/` estilos e imágenes; `js/` lógica de navegador; `database/` esquema; `data/` persistencia generada; `documentacion/` manuales; `server.js` API y servidor.

## Respaldo y restauración
1. Detener el servidor para una copia consistente.
2. Copiar `data/stepstyle.sqlite` a una ubicación protegida.
3. Copiar también `sessions.sqlite` solo si se requiere conservar sesiones; normalmente no es necesario.
4. Para restaurar, detener el servidor y reemplazar `data/stepstyle.sqlite` por el respaldo.
5. Iniciar y verificar `/api/health`, catálogo, pedidos e inventario.
6. Documentar fecha, responsable y resultado de la prueba.

No publicar respaldos con datos personales en repositorios públicos.

## Mantenimiento
- Actualizar dependencias con revisión previa.
- Revisar logs de ejecución y espacio disponible.
- Respaldar antes de actualizar.
- Cambiar credenciales y secretos expuestos.
- Revisar permisos de archivos y configurar HTTPS detrás de un proxy seguro para despliegue.
- Configurar almacenamiento persistente: algunos hostings efímeros borran archivos SQLite al reiniciar.

## Solución de problemas
- `npm` no reconocido: instalar Node.js LTS y reiniciar terminal.
- Puerto ocupado: cambiar `PORT` en `.env`.
- Error al compilar better-sqlite3: usar Node.js LTS compatible y herramientas de compilación del sistema.
- Login no funciona: verificar que el backend está iniciado y que el navegador accede al mismo origen.
- GitHub Pages no permite `/api`: desplegar backend por separado y configurar CORS/origen y cookies de forma segura; esta entrega está configurada para mismo origen.
