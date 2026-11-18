#!/usr/bin/env python3
"""Prueba de punta a punta de la API de StepStyle.

Uso:  python3 backend/tests/e2e_api.py http://127.0.0.1:8000 admin@correo 'clave-admin'
Cubre: catálogo, registro/login, compra, idempotencia, inventario insuficiente,
cupón, consulta de pedido en admin, cambio de estado, cancelación con reposición
de stock, devolución y bloqueo de rutas admin a clientes.
"""
import json, sys, uuid, urllib.request, urllib.error

BASE, ADMIN_EMAIL, ADMIN_PASS = sys.argv[1].rstrip('/'), sys.argv[2], sys.argv[3]
ORIGIN = sys.argv[4] if len(sys.argv) > 4 else None
ok = fail = 0


def call(path, method='GET', data=None, token=None, headers=None):
    h = {'Content-Type': 'application/json', **(headers or {})}
    if token:
        h['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(BASE + '/api' + path, method=method, headers=h,
                                 data=json.dumps(data).encode() if data is not None else None)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read() or b'{}'), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'{}'), dict(e.headers)


def check(name, cond, extra=''):
    global ok, fail
    ok, fail = (ok + 1, fail) if cond else (ok, fail + 1)
    print(('  OK   ' if cond else '  FALLA ') + name + (f'  -> {extra}' if extra and not cond else ''))


s, d, _ = call('/health'); check('health', s == 200 and d.get('ok'), d); print('     motor:', d.get('db'))
s, products, _ = call('/products'); check('catálogo con 15 productos', s == 200 and len(products) >= 15, s)
p = products[0]; pid = p['id']

email = f'cliente+{uuid.uuid4().hex[:8]}@stepstyle.test'
s, d, _ = call('/auth/register', 'POST', {'name': 'Cliente Prueba', 'email': email, 'password': 'ClaveSegura123'})
check('registro', s == 201, d)
s, d, _ = call('/auth/register', 'POST', {'name': 'Cliente Prueba', 'email': email, 'password': 'ClaveSegura123'})
check('registro duplicado rechazado', s == 400, d)
s, d, _ = call('/auth/login', 'POST', {'email': email, 'password': 'mala'}); check('login con clave incorrecta rechazado', s == 401, d)
s, d, _ = call('/auth/login', 'POST', {'email': email, 'password': 'ClaveSegura123'}); check('login cliente', s == 200 and d.get('token'), d)
tok = d['token']
s, d, _ = call('/me', token=tok); check('/me', s == 200 and d['email'] == email, d)
s, d, _ = call('/admin/orders', token=tok); check('cliente bloqueado en admin', s == 403, d)

ship = {'name': 'Cliente Prueba', 'email': email, 'address': 'Calle 1', 'city': 'Nuevo Laredo', 'state': 'Tamaulipas', 'zip': '88000', 'phone': '8670000000'}
key = uuid.uuid4().hex
order = {'items': [{'id': pid, 'quantity': 1}], 'shipping': ship, 'payment': 'Simulado', 'accept_terms': True, 'coupon': 'STEP10', 'idempotency_key': key}
s, d, _ = call('/orders', 'POST', dict(order, accept_terms=False), token=tok); check('pedido sin aceptar términos rechazado', s == 400, d)
s, o1, _ = call('/orders', 'POST', order, token=tok); check('compra con cupón', s == 201 and o1.get('folio', '').startswith('ST-'), o1)
s, o2, _ = call('/orders', 'POST', order, token=tok); check('idempotencia (mismo folio)', s == 200 and o2.get('folio') == o1.get('folio'), o2)
s, after, _ = call('/products'); stock_after = next(x['stock'] for x in after if x['id'] == pid)
check('stock descontado', stock_after == p['stock'] - 1, (p['stock'], stock_after))
s, d, _ = call('/orders', 'POST', dict(order, items=[{'id': pid, 'quantity': 99}], idempotency_key=uuid.uuid4().hex), token=tok)
check('inventario insuficiente rechazado', s == 400 and 'Inventario' in d.get('error', ''), d)
s, mine, _ = call('/orders', token=tok); check('historial del cliente', s == 200 and len(mine) == 1, mine)
oid = mine[0]['id']

s, d, _ = call('/auth/login', 'POST', {'email': ADMIN_EMAIL, 'password': ADMIN_PASS}); check('login admin', s == 200 and d['user']['role'] == 'admin', d)
adm = d.get('token')
s, d, _ = call(f'/admin/orders/{oid}', token=adm); check('admin ve detalle del pedido', s == 200 and d['items'][0]['product_id'] == pid, d)
s, d, _ = call(f'/admin/orders/{oid}', 'PATCH', {'status': 'entregado'}, token=adm); check('transición inválida rechazada', s == 400, d)
s, d, _ = call(f'/admin/orders/{oid}', 'PATCH', {'status': 'preparando'}, token=adm); check('pedido -> preparando', s == 200, d)
s, d, _ = call(f'/admin/orders/{oid}', 'PATCH', {'status': 'cancelado'}, token=adm); check('pedido -> cancelado', s == 200, d)
s, after, _ = call('/products'); check('stock repuesto al cancelar', next(x['stock'] for x in after if x['id'] == pid) == p['stock'], '')

s, d, _ = call('/returns', 'POST', {'order_id': oid, 'reason': 'La talla no me quedó'}, token=tok); check('solicitar devolución', s == 201, d)
rid = d.get('id')
s, d, _ = call('/returns', 'POST', {'order_id': oid, 'reason': 'La talla no me quedó'}, token=tok); check('devolución duplicada rechazada', s == 400, d)
s, d, _ = call(f'/admin/returns/{rid}', 'PATCH', {'status': 'aprobada'}, token=adm); check('admin aprueba devolución', s == 200, d)

sku = 'T-' + uuid.uuid4().hex[:6].upper()
s, d, _ = call('/admin/products', 'POST', {'id': sku, 'name': 'Tenis prueba', 'category': 'Tenis', 'price_cents': 99900, 'stock': 5}, token=adm); check('alta de producto', s == 201, d)
s, d, _ = call(f'/admin/products/{sku}', 'PATCH', {'stock': 8, 'reason': 'reabasto'}, token=adm); check('ajuste de inventario', s == 200, d)
s, d, _ = call(f'/admin/products/{sku}', 'PATCH', {'stock': -1}, token=adm); check('stock negativo rechazado', s == 400, d)
s, d, _ = call('/admin/inventory', token=adm); check('movimientos de inventario', s == 200 and any(x['reason'] == 'reabasto' for x in d), '')
s, d, _ = call('/admin/audit', token=adm); check('bitácora', s == 200 and len(d) >= 4, len(d) if isinstance(d, list) else d)
s, d, _ = call('/admin/reports', token=adm); check('reportes', s == 200 and d['orders'] >= 1, d)
s, d, _ = call(f'/admin/products/{sku}', 'PATCH', {'active': 0}, token=adm)

if ORIGIN:
    s, d, h = call('/products', headers={'Origin': ORIGIN}); check('CORS para ' + ORIGIN, h.get('Access-Control-Allow-Origin') == ORIGIN, h)
    s, d, h = call('/products', headers={'Origin': 'https://sitio-ajeno.com'}); check('CORS bloquea otros orígenes', 'Access-Control-Allow-Origin' not in h, h)

s, d, _ = call('/auth/logout', 'POST', {}, token=tok)
s, d, _ = call('/me', token=tok); check('token invalidado tras logout', s == 403, d)

print(f'\n{ok} correctas, {fail} fallidas')
sys.exit(1 if fail else 0)
