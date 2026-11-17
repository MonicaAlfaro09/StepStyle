# Ficha técnica del sistema

| Campo | Descripción |
|---|---|
| Nombre | StepStyle |
| Versión | 1.0.0 académica |
| Propósito | Tienda demostrativa de calzado moderno para hombres y mujeres |
| Modelo | B2C simulado |
| Arquitectura | Aplicación web cliente-servidor; frontend estático y API REST |
| Frontend | HTML5, CSS3 y JavaScript |
| Backend | Node.js + Express 4 |
| Base de datos | SQLite mediante better-sqlite3 |
| Autenticación | Sesión de servidor con cookie HttpOnly/SameSite y hash bcrypt |
| Roles | customer y admin |
| Moneda | MXN |
| Catálogo | 15 productos iniciales |
| Pago | Simulación académica; sin PAN/CVV |
| Ejecución | Node.js 20+, `npm install`, `npm start` |
| URL local | http://localhost:3000 |
| API health | GET /api/health |
| Persistencia | `data/stepstyle.sqlite` y `sessions.sqlite` |
| Repositorio | Agregar URL del repositorio del equipo |
| Responsables | Completar nombres de integrantes |
| Fecha | 17 de noviembre de 2026 |

## Limitaciones conocidas
No se integró pasarela bancaria real, proveedor de paquetería, correo transaccional, CFDI ni recuperación de contraseña por correo. No hay entorno productivo certificado. La tienda no debe utilizarse para ventas reales sin completar controles, revisión jurídica, privacidad, despliegue HTTPS, monitoreo y pruebas de seguridad independientes.
