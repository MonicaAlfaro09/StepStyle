#!/usr/bin/env python3
"""StepStyle · backend académico.

- Local:      SQLite (sin dependencias)   ->  python3 backend/server.py
- Producción: PostgreSQL (Neon) en Render ->  define DATABASE_URL

Variables de entorno:
  DATABASE_URL              Cadena de conexión PostgreSQL. Si no existe, se usa SQLite.
  STEPSTYLE_DB              Ruta del archivo SQLite (solo modo local).
  ALLOWED_ORIGINS           Orígenes permitidos para CORS, separados por coma.
  STEPSTYLE_ADMIN_EMAIL     Correo de la cuenta administradora inicial.
  STEPSTYLE_ADMIN_PASSWORD  Contraseña inicial (mínimo 12 caracteres).
  HOST / PORT               Interfaz y puerto (Render define PORT automáticamente).
"""
import os, json, sqlite3, hashlib, hmac, secrets, time, re, threading, datetime, logging
from contextlib import contextmanager, nullcontext
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('stepstyle')

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / 'backend'
DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()
PG = bool(DATABASE_URL)
SQLITE_PATH = Path(os.environ.get('STEPSTYLE_DB', str(BACKEND / 'stepstyle.sqlite3')))
LOCK = threading.RLock()          # serializa pedidos en SQLite (en PostgreSQL se usa FOR UPDATE)
SESSION_HOURS = 8
DEFAULT_ORIGINS = 'https://monicaalfaro09.github.io,http://127.0.0.1:8000,http://localhost:8000'
ALLOWED_ORIGINS = {o.strip().rstrip('/') for o in os.environ.get('ALLOWED_ORIGINS', DEFAULT_ORIGINS).split(',') if o.strip()}

if PG:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool
    POOL = ConnectionPool(DATABASE_URL, min_size=1, max_size=5, open=True,
                          kwargs={'row_factory': dict_row},
                          check=ConnectionPool.check_connection)
    IntegrityError = psycopg.IntegrityError
else:
    IntegrityError = sqlite3.IntegrityError


# ---------------------------------------------------------------- base de datos
class DB:
    """Envoltura mínima para usar el mismo SQL ('?' como marcador) en SQLite y PostgreSQL."""
    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, params=()):
        if PG:
            sql = sql.replace('?', '%s')
        return self.conn.execute(sql, params)

    def one(self, sql, params=()):
        return self.execute(sql, params).fetchone()

    def all(self, sql, params=()):
        return self.execute(sql, params).fetchall()

    def insert(self, sql, params=()):
        """INSERT que devuelve el id generado."""
        if PG:
            return self.execute(sql + ' RETURNING id', params).fetchone()['id']
        return self.execute(sql, params).lastrowid


@contextmanager
def db():
    """Abre una transacción: confirma al terminar o revierte si hay error."""
    if PG:
        with POOL.connection() as conn:   # el pool confirma o revierte automáticamente
            yield DB(conn)
        return
    conn = sqlite3.connect(SQLITE_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    conn.execute('PRAGMA busy_timeout=20000')
    try:
        yield DB(conn)
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def row(r):
    """Convierte una fila a dict serializable (fechas a ISO 8601)."""
    if r is None:
        return None
    out = dict(r)
    for k, v in out.items():
        if isinstance(v, (datetime.datetime, datetime.date)):
            out[k] = v.isoformat()
    return out


def meta(value):
    return value if isinstance(value, dict) else json.loads(value)


SQLITE_SCHEMA = '''
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'customer');
CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,expires_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS products(id TEXT PRIMARY KEY,name TEXT NOT NULL,category TEXT NOT NULL,price_cents INTEGER NOT NULL CHECK(price_cents>=0),discount INTEGER NOT NULL DEFAULT 0 CHECK(discount BETWEEN 0 AND 100),stock INTEGER NOT NULL CHECK(stock>=0),active INTEGER NOT NULL DEFAULT 1,metadata TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY,folio TEXT UNIQUE NOT NULL,user_id INTEGER NOT NULL REFERENCES users(id),created_at TEXT NOT NULL,shipping TEXT NOT NULL,subtotal_cents INTEGER NOT NULL,tax_cents INTEGER NOT NULL,shipping_cents INTEGER NOT NULL,total_cents INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'pendiente',payment_status TEXT NOT NULL DEFAULT 'aprobado',coupon TEXT,terms_version TEXT NOT NULL,terms_accepted_at TEXT NOT NULL,idempotency_key TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY,order_id INTEGER NOT NULL REFERENCES orders(id),product_id TEXT NOT NULL,sku TEXT NOT NULL,name TEXT NOT NULL,quantity INTEGER NOT NULL CHECK(quantity>0),unit_price_cents INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS inventory_movements(id INTEGER PRIMARY KEY,product_id TEXT NOT NULL,quantity INTEGER NOT NULL,reason TEXT NOT NULL,order_id INTEGER,actor_id INTEGER,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS returns(id INTEGER PRIMARY KEY,order_id INTEGER NOT NULL REFERENCES orders(id),user_id INTEGER NOT NULL REFERENCES users(id),reason TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'solicitada',created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY,actor_id INTEGER,action TEXT NOT NULL,entity TEXT NOT NULL,entity_id TEXT,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS coupons(code TEXT PRIMARY KEY,percent INTEGER NOT NULL,active INTEGER NOT NULL DEFAULT 1);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_returns_order ON returns(order_id);
'''


def migrate_pg(c):
    """Aplica en orden los archivos backend/migrations/NNN_*.sql que falten."""
    c.execute('CREATE TABLE IF NOT EXISTS schema_migrations(version VARCHAR(100) PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())')
    done = {r['version'] for r in c.all('SELECT version FROM schema_migrations')}
    for f in sorted((BACKEND / 'migrations').glob('*.sql')):
        if f.name not in done:
            log.info('Aplicando migración %s', f.name)
            c.conn.execute(f.read_text(encoding='utf-8'))
            c.execute('INSERT INTO schema_migrations(version) VALUES(?)', (f.name,))


def init():
    with db() as c:
        if PG:
            c.execute('SELECT pg_advisory_xact_lock(424242)')   # evita migraciones simultáneas
            migrate_pg(c)
        else:
            SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
            c.conn.executescript(SQLITE_SCHEMA)
        seed(c)


def seed(c):
    if c.one('SELECT COUNT(*) AS n FROM products')['n'] == 0:
        for p in json.loads((BACKEND / 'seed_products.json').read_text(encoding='utf-8')):
            c.execute('INSERT INTO products(id,name,category,price_cents,discount,stock,metadata) VALUES(?,?,?,?,?,?,?)',
                      (p['id'], p['name'], p['category'], round(p['price'] * 100), p.get('discount', 0), p['stock'], json.dumps(p, ensure_ascii=False)))
        log.info('Productos semilla cargados')
    if c.one('SELECT COUNT(*) AS n FROM coupons')['n'] == 0:
        c.execute('INSERT INTO coupons(code,percent) VALUES(?,?)', ('STEP10', 10))
    if c.one('SELECT COUNT(*) AS n FROM users WHERE role=?', ('admin',))['n'] == 0:
        email = os.environ.get('STEPSTYLE_ADMIN_EMAIL'); password = os.environ.get('STEPSTYLE_ADMIN_PASSWORD')
        if email and password and len(password) >= 12:
            c.execute('INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)', ('Administrador', email.strip().lower(), pw_hash(password), 'admin'))
            log.info('Cuenta administradora creada')
        else:
            log.warning('No hay administrador: define STEPSTYLE_ADMIN_EMAIL y STEPSTYLE_ADMIN_PASSWORD (12+ caracteres)')


# ---------------------------------------------------------------- seguridad
def pw_hash(p):
    salt = secrets.token_bytes(16); digest = hashlib.pbkdf2_hmac('sha256', p.encode(), salt, 250000)
    return 'pbkdf2_sha256$250000$' + salt.hex() + '$' + digest.hex()


def verify(p, stored):
    try:
        alg, n, s, h = stored.split('$')
        return alg == 'pbkdf2_sha256' and hmac.compare_digest(hashlib.pbkdf2_hmac('sha256', p.encode(), bytes.fromhex(s), int(n)), bytes.fromhex(h))
    except (ValueError, TypeError):
        return False


def token_hash(token):
    """En la base solo se guarda el hash del token, nunca el token."""
    return hashlib.sha256(token.encode()).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def in_hours(h):
    return (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=h)).isoformat()


class RateLimiter:
    """Límite simple en memoria: N intentos por ventana y por clave (IP)."""
    def __init__(self, limit, window):
        self.limit, self.window, self.hits, self.lock = limit, window, {}, threading.Lock()

    def allow(self, key):
        t = time.time()
        with self.lock:
            hits = [x for x in self.hits.get(key, []) if t - x < self.window]
            allowed = len(hits) < self.limit
            if allowed:
                hits.append(t)
            self.hits[key] = hits
            return allowed


LOGIN_LIMIT = RateLimiter(10, 15 * 60)      # 10 intentos de login cada 15 min por IP
REGISTER_LIMIT = RateLimiter(5, 60 * 60)    # 5 registros por hora por IP


# ---------------------------------------------------------------- HTTP
class Handler(SimpleHTTPRequestHandler):
    server_version = 'StepStyle'
    sys_version = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def client_ip(self):
        fwd = self.headers.get('X-Forwarded-For', '') if getattr(self, 'headers', None) else ''
        return fwd.split(',')[0].strip() or self.client_address[0]

    def cors(self):
        origin = (self.headers.get('Origin') or '').rstrip('/')
        if origin in ALLOWED_ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Vary', 'Origin')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            self.send_header('Access-Control-Max-Age', '600')

    def reply(self, code, data):
        raw = json.dumps(data, ensure_ascii=False, default=str).encode()
        self.send_response(code)
        self.cors()
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def body(self):
        size = int(self.headers.get('Content-Length', '0'))
        if size > 65536:
            raise ValueError('Solicitud demasiado grande')
        data = json.loads(self.rfile.read(size)) if size else {}
        if not isinstance(data, dict):
            raise ValueError('Formato inválido')
        return data

    def token(self):
        return self.headers.get('Authorization', '').removeprefix('Bearer ').strip()

    def user(self, c):
        tok = self.token()
        if not tok:
            return None
        return c.one('SELECT u.id,u.name,u.email,u.role FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>?',
                     (token_hash(tok), now()))

    def require(self, c, admin=False):
        u = self.user(c)
        if not u:
            raise PermissionError('Inicia sesión')
        if admin and u['role'] != 'admin':
            raise PermissionError('Sin permisos')
        return u

    def do_OPTIONS(self):
        self.send_response(204)
        self.cors()
        self.send_header('Content-Length', '0')
        self.end_headers()

    # ---------------------------------------------------------- lectura
    def do_GET(self):
        path = urlparse(self.path).path
        if not path.startswith('/api/'):
            if path.startswith(('/backend', '/.git', '/.env')):
                return self.send_error(403)
            return super().do_GET()
        try:
            with db() as c:
                if path == '/api/health':
                    c.one('SELECT 1 AS ok')
                    return self.reply(200, {'ok': True, 'db': 'postgresql' if PG else 'sqlite'})
                if path == '/api/products':
                    rows = c.all('SELECT * FROM products WHERE active=1 ORDER BY id')
                    return self.reply(200, [dict(meta(x['metadata']), price=x['price_cents'] / 100, stock=x['stock'], discount=x['discount']) for x in rows])
                if path == '/api/me':
                    return self.reply(200, row(self.require(c)))
                if path == '/api/orders':
                    u = self.require(c)
                    return self.reply(200, [row(x) for x in c.all('SELECT * FROM orders WHERE user_id=? ORDER BY id DESC', (u['id'],))])
                if path == '/api/returns':
                    u = self.require(c)
                    return self.reply(200, [row(x) for x in c.all('SELECT * FROM returns WHERE user_id=? ORDER BY id DESC', (u['id'],))])
                if path == '/api/admin/orders':
                    self.require(c, True)
                    return self.reply(200, [row(x) for x in c.all('SELECT * FROM orders ORDER BY id DESC')])
                m = re.fullmatch(r'/api/admin/orders/(\d+)', path)
                if m:
                    self.require(c, True)
                    order = c.one('SELECT * FROM orders WHERE id=?', (int(m.group(1)),))
                    if not order:
                        return self.reply(404, {'error': 'Pedido inexistente'})
                    items = c.all('SELECT * FROM order_items WHERE order_id=? ORDER BY id', (order['id'],))
                    return self.reply(200, dict(row(order), items=[row(x) for x in items]))
                if path == '/api/admin/products':
                    self.require(c, True)
                    return self.reply(200, [row(x) for x in c.all('SELECT id,name,category,price_cents,discount,stock,active FROM products ORDER BY id')])
                if path == '/api/admin/returns':
                    self.require(c, True)
                    return self.reply(200, [row(x) for x in c.all('SELECT * FROM returns ORDER BY id DESC')])
                if path == '/api/admin/inventory':
                    self.require(c, True)
                    return self.reply(200, [row(x) for x in c.all('SELECT * FROM inventory_movements ORDER BY id DESC LIMIT 200')])
                if path == '/api/admin/audit':
                    self.require(c, True)
                    return self.reply(200, [row(x) for x in c.all('SELECT * FROM audit_logs ORDER BY id DESC LIMIT 200')])
                if path == '/api/admin/reports':
                    self.require(c, True)
                    return self.reply(200, {
                        'orders': c.one('SELECT COUNT(*) AS n FROM orders')['n'],
                        'sales_cents': c.one("SELECT COALESCE(SUM(total_cents),0) AS n FROM orders WHERE status!='cancelado'")['n'],
                        'low_stock': c.one('SELECT COUNT(*) AS n FROM products WHERE stock<=3 AND active=1')['n'],
                        'returns': c.one('SELECT COUNT(*) AS n FROM returns')['n'],
                    })
            return self.reply(404, {'error': 'No encontrado'})
        except PermissionError as e:
            return self.reply(403, {'error': str(e)})
        except Exception:
            log.exception('Error en GET %s', path)
            return self.reply(500, {'error': 'Error interno'})

    # ---------------------------------------------------------- escritura
    def do_POST(self):
        return self.change('POST')

    def do_PATCH(self):
        return self.change('PATCH')

    def change(self, method):
        path = urlparse(self.path).path
        if not path.startswith('/api/'):
            return self.reply(404, {'error': 'No encontrado'})
        try:
            d = self.body()
            if path == '/api/auth/register':
                return self.register(d)
            if path == '/api/auth/login':
                return self.login(d)
            if path == '/api/auth/logout':
                with db() as c:
                    c.execute('DELETE FROM sessions WHERE token_hash=?', (token_hash(self.token()),))
                return self.reply(200, {'ok': True})
            if path == '/api/orders' and method == 'POST':
                return self.create_order(d)
            result = (404, {'error': 'No encontrado'})
            with db() as c:   # se responde después de confirmar la transacción
                u = self.require(c)
                if path == '/api/returns' and method == 'POST':
                    result = self.create_return(c, u, d)
                elif path.startswith('/api/admin/'):
                    if u['role'] != 'admin':
                        raise PermissionError('Sin permisos')
                    result = self.admin_change(c, u, path, method, d)
            return self.reply(*result)
        except PermissionError as e:
            return self.reply(403, {'error': str(e)})
        except IntegrityError:
            return self.reply(400, {'error': 'El registro ya existe o viola una restricción'})
        except (ValueError, KeyError, TypeError) as e:
            return self.reply(400, {'error': str(e)})
        except Exception:
            log.exception('Error en %s %s', method, path)
            return self.reply(500, {'error': 'Error interno'})

    def register(self, d):
        if not REGISTER_LIMIT.allow(self.client_ip()):
            return self.reply(429, {'error': 'Demasiados registros, intenta más tarde'})
        email = str(d.get('email', '')).strip().lower(); password = str(d.get('password', '')); name = str(d.get('name', '')).strip()
        if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email) or len(email) > 254 or not 10 <= len(password) <= 200 or len(name) < 2:
            raise ValueError('Revisa nombre, correo y contraseña (mínimo 10 caracteres)')
        try:
            with db() as c:
                c.execute('INSERT INTO users(name,email,password_hash) VALUES(?,?,?)', (name[:100], email, pw_hash(password)))
        except IntegrityError:
            raise ValueError('El correo ya está registrado')
        return self.reply(201, {'ok': True})

    def login(self, d):
        if not LOGIN_LIMIT.allow(self.client_ip()):
            return self.reply(429, {'error': 'Demasiados intentos, espera 15 minutos'})
        with db() as c:
            u = c.one('SELECT * FROM users WHERE email=?', (str(d.get('email', '')).strip().lower(),))
            if not u or not verify(str(d.get('password', '')), u['password_hash']):
                return self.reply(401, {'error': 'Credenciales incorrectas'})
            token = secrets.token_urlsafe(32)
            c.execute('DELETE FROM sessions WHERE expires_at<?', (now(),))
            c.execute('INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,?)', (token_hash(token), u['id'], in_hours(SESSION_HOURS)))
        return self.reply(200, {'token': token, 'user': {'name': u['name'], 'email': u['email'], 'role': u['role']}})

    def create_return(self, c, u, d):
        oid = int(d.get('order_id', 0)); reason = str(d.get('reason', '')).strip()[:500]
        if len(reason) < 8:
            raise ValueError('Indica el motivo')
        if not c.one('SELECT id FROM orders WHERE id=? AND user_id=?', (oid, u['id'])):
            raise PermissionError('Pedido no disponible')
        if c.one("SELECT id FROM returns WHERE order_id=? AND status='solicitada'", (oid,)):
            raise ValueError('Ya existe una solicitud abierta para este pedido')
        rid = c.insert('INSERT INTO returns(order_id,user_id,reason,created_at) VALUES(?,?,?,?)', (oid, u['id'], reason, now()))
        return (201, {'id': rid, 'status': 'solicitada'})

    def create_order(self, d):
        lines = d.get('items', []); key = str(d.get('idempotency_key', ''))
        if not isinstance(lines, list) or not 1 <= len(lines) <= 50 or not 12 <= len(key) <= 100 or not d.get('accept_terms'):
            raise ValueError('Pedido o aceptación inválidos')
        ship = d.get('shipping', {}); required = ['name', 'email', 'address', 'city', 'state', 'zip', 'phone']
        if not isinstance(ship, dict) or any(not str(ship.get(x, '')).strip() for x in required) or not re.fullmatch(r'\d{5}', str(ship.get('zip', ''))):
            raise ValueError('Datos de entrega incompletos')
        ship = {x: str(ship.get(x, '')).strip()[:200] for x in required}
        if d.get('payment') not in ('Simulado', 'Transferencia', 'Tarjeta'):
            raise ValueError('Método de pago inválido')
        with (nullcontext() if PG else LOCK):
            with db() as c:
                u = self.require(c)
                if not PG:
                    c.execute('BEGIN IMMEDIATE')
                old = c.one('SELECT * FROM orders WHERE idempotency_key=? AND user_id=?', (key, u['id']))
                if old:
                    return self.reply(200, {'folio': old['folio'], 'total': old['total_cents'] / 100, 'status': old['status']})
                subtotal = 0; resolved = []; seen = set()
                for item in lines:
                    if not isinstance(item, dict):
                        raise ValueError('Artículo inválido')
                    pid = str(item.get('id', '')); qty = int(item.get('quantity', 0))
                    if pid in seen:
                        raise ValueError('Producto duplicado en carrito')
                    seen.add(pid)
                    if qty < 1 or qty > 99:
                        raise ValueError('Cantidad inválida')
                    # FOR UPDATE bloquea la fila del producto en PostgreSQL hasta terminar la transacción
                    p = c.one('SELECT * FROM products WHERE id=? AND active=1' + (' FOR UPDATE' if PG else ''), (pid,))
                    if not p or p['stock'] < qty:
                        raise ValueError('Inventario insuficiente: ' + pid)
                    unit = (p['price_cents'] * (100 - p['discount']) + 50) // 100
                    subtotal += unit * qty; resolved.append((p, qty, unit))
                discount = 0; coupon = str(d.get('coupon', '')).strip().upper()[:30]
                if coupon:
                    cp = c.one('SELECT percent FROM coupons WHERE code=? AND active=1', (coupon,))
                    if not cp:
                        raise ValueError('Cupón inválido')
                    discount = (subtotal * cp['percent'] + 50) // 100
                base = subtotal - discount; tax = (base * 16 + 50) // 100
                delivery = 0 if subtotal >= 250000 else 14900
                total = base + tax + delivery; folio = 'ST-' + secrets.token_hex(5).upper(); ts = now()
                oid = c.insert('INSERT INTO orders(folio,user_id,created_at,shipping,subtotal_cents,tax_cents,shipping_cents,total_cents,coupon,terms_version,terms_accepted_at,idempotency_key) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                               (folio, u['id'], ts, json.dumps(ship, ensure_ascii=False), subtotal, tax, delivery, total, coupon or None, '1.0', ts, key))
                for p, qty, unit in resolved:
                    if c.execute('UPDATE products SET stock=stock-? WHERE id=? AND stock>=?', (qty, p['id'], qty)).rowcount != 1:
                        raise ValueError('Inventario insuficiente')
                    c.execute('INSERT INTO order_items(order_id,product_id,sku,name,quantity,unit_price_cents) VALUES(?,?,?,?,?,?)', (oid, p['id'], p['id'], p['name'], qty, unit))
                    c.execute('INSERT INTO inventory_movements(product_id,quantity,reason,order_id,actor_id,created_at) VALUES(?,?,?,?,?,?)', (p['id'], -qty, 'venta', oid, u['id'], ts))
                c.execute('INSERT INTO audit_logs(actor_id,action,entity,entity_id,created_at) VALUES(?,?,?,?,?)', (u['id'], 'crear', 'pedido', str(oid), ts))
        return self.reply(201, {'id': oid, 'folio': folio, 'total': total / 100, 'subtotal': subtotal / 100, 'discount': discount / 100, 'tax': tax / 100, 'shipping': delivery / 100, 'status': 'pendiente', 'date': ts})

    def admin_change(self, c, u, path, method, d):
        def audit(action, entity, eid):
            c.execute('INSERT INTO audit_logs(actor_id,action,entity,entity_id,created_at) VALUES(?,?,?,?,?)', (u['id'], action, entity, str(eid), now()))

        if path == '/api/admin/products' and method == 'POST':
            pid = str(d.get('id', '')).strip().upper(); name = str(d.get('name', '')).strip()[:150]; cat = str(d.get('category', '')).strip()[:50]
            price = int(d.get('price_cents', -1)); stock = int(d.get('stock', -1))
            if not re.fullmatch(r'[A-Za-z0-9-]{2,24}', pid) or not name or not cat or price < 0 or stock < 0:
                raise ValueError('Producto inválido')
            if c.one('SELECT id FROM products WHERE id=?', (pid,)):
                raise ValueError('Ya existe un producto con ese SKU')
            m = {'id': pid, 'name': name, 'category': cat, 'brand': 'StepStyle', 'gender': 'Unisex', 'style': 'Casual', 'price': price / 100, 'discount': 0, 'stock': stock, 'image': '', 'sizes': [25, 26, 27], 'colors': ['Negro'], 'description': '', 'specs': []}
            c.execute('INSERT INTO products(id,name,category,price_cents,stock,metadata) VALUES(?,?,?,?,?,?)', (pid, name, cat, price, stock, json.dumps(m, ensure_ascii=False)))
            if stock:
                c.execute('INSERT INTO inventory_movements(product_id,quantity,reason,actor_id,created_at) VALUES(?,?,?,?,?)', (pid, stock, 'alta', u['id'], now()))
            audit('crear', 'producto', pid)
            return (201, {'ok': True})

        m = re.fullmatch(r'/api/admin/products/([A-Za-z0-9-]+)', path)
        if m and method == 'PATCH':
            pid = m.group(1); old = c.one('SELECT * FROM products WHERE id=?' + (' FOR UPDATE' if PG else ''), (pid,))
            if not old:
                raise ValueError('Producto inexistente')
            price = int(d.get('price_cents', old['price_cents'])); stock = int(d.get('stock', old['stock']))
            active = int(d.get('active', old['active'])); discount = int(d.get('discount', old['discount']))
            if price < 0 or stock < 0 or active not in (0, 1) or not 0 <= discount <= 100:
                raise ValueError('Valores inválidos')
            c.execute('UPDATE products SET price_cents=?,stock=?,active=?,discount=? WHERE id=?', (price, stock, active, discount, pid))
            delta = stock - old['stock']
            if delta:
                reason = str(d.get('reason', '')).strip()[:50] or 'ajuste'
                c.execute('INSERT INTO inventory_movements(product_id,quantity,reason,actor_id,created_at) VALUES(?,?,?,?,?)', (pid, delta, reason, u['id'], now()))
            audit('editar', 'producto', pid)
            return (200, {'ok': True})

        m = re.fullmatch(r'/api/admin/orders/(\d+)', path)
        if m and method == 'PATCH':
            oid = int(m.group(1)); status = str(d.get('status', ''))
            allowed = {'pendiente': ['preparando', 'cancelado'], 'preparando': ['enviado', 'cancelado'], 'enviado': ['entregado'], 'entregado': [], 'cancelado': []}
            old = c.one('SELECT status FROM orders WHERE id=?' + (' FOR UPDATE' if PG else ''), (oid,))
            if not old or status not in allowed.get(old['status'], []):
                raise ValueError('Transición de pedido no válida')
            c.execute('UPDATE orders SET status=? WHERE id=?', (status, oid))
            if status == 'cancelado':
                for x in c.all('SELECT product_id,quantity FROM order_items WHERE order_id=?', (oid,)):
                    c.execute('UPDATE products SET stock=stock+? WHERE id=?', (x['quantity'], x['product_id']))
                    c.execute('INSERT INTO inventory_movements(product_id,quantity,reason,order_id,actor_id,created_at) VALUES(?,?,?,?,?,?)', (x['product_id'], x['quantity'], 'cancelación', oid, u['id'], now()))
            audit('estado ' + status, 'pedido', oid)
            return (200, {'ok': True})

        m = re.fullmatch(r'/api/admin/returns/(\d+)', path)
        if m and method == 'PATCH':
            rid = int(m.group(1)); status = str(d.get('status', ''))
            if status not in ('aprobada', 'rechazada'):
                raise ValueError('Estado inválido')
            old = c.one('SELECT status FROM returns WHERE id=?', (rid,))
            if not old or old['status'] != 'solicitada':
                raise ValueError('Solicitud no disponible')
            c.execute('UPDATE returns SET status=? WHERE id=?', (status, rid))
            audit('resolver ' + status, 'devolución', rid)
            return (200, {'ok': True})
        return (404, {'error': 'No encontrado'})


if __name__ == '__main__':
    init()
    port = int(os.environ.get('PORT', '8000'))
    host = os.environ.get('HOST', '0.0.0.0' if os.environ.get('RENDER') else '127.0.0.1')
    log.info('StepStyle (%s) escuchando en http://%s:%s/', 'PostgreSQL' if PG else 'SQLite', host, port)
    ThreadingHTTPServer((host, port), Handler).serve_forever()
