#!/usr/bin/env python3
# StepStyle academic backend: stdlib HTTP + SQLite
import os,json,sqlite3,hashlib,hmac,secrets,time,re,threading,datetime
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlparse,parse_qs
from http import HTTPStatus
ROOT=Path(__file__).resolve().parent.parent
DB=Path(os.environ.get('STEPSTYLE_DB',str(ROOT/'backend'/'stepstyle.sqlite3')))
LOCK=threading.RLock()
SESSIONS={}
def db():
 c=sqlite3.connect(DB,timeout=20);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA busy_timeout=20000');return c
def pw_hash(p):
 salt=secrets.token_bytes(16);digest=hashlib.pbkdf2_hmac('sha256',p.encode(),salt,250000)
 return 'pbkdf2_sha256$250000$'+salt.hex()+'$'+digest.hex()
def verify(p,stored):
 try:
  alg,n,s,h=stored.split('$');return alg=='pbkdf2_sha256' and hmac.compare_digest(hashlib.pbkdf2_hmac('sha256',p.encode(),bytes.fromhex(s),int(n)),bytes.fromhex(h))
 except (ValueError,TypeError):return False
def init():
 DB.parent.mkdir(parents=True,exist_ok=True)
 with db() as c:
  c.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'customer');
CREATE TABLE IF NOT EXISTS products(id TEXT PRIMARY KEY,name TEXT NOT NULL,category TEXT NOT NULL,price_cents INTEGER NOT NULL CHECK(price_cents>=0),discount INTEGER NOT NULL DEFAULT 0 CHECK(discount BETWEEN 0 AND 100),stock INTEGER NOT NULL CHECK(stock>=0),active INTEGER NOT NULL DEFAULT 1,metadata TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY,folio TEXT UNIQUE NOT NULL,user_id INTEGER NOT NULL REFERENCES users(id),created_at TEXT NOT NULL,shipping TEXT NOT NULL,subtotal_cents INTEGER NOT NULL,tax_cents INTEGER NOT NULL,shipping_cents INTEGER NOT NULL,total_cents INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'pendiente',payment_status TEXT NOT NULL DEFAULT 'aprobado',coupon TEXT,terms_version TEXT NOT NULL,terms_accepted_at TEXT NOT NULL,idempotency_key TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY,order_id INTEGER NOT NULL REFERENCES orders(id),product_id TEXT NOT NULL,sku TEXT NOT NULL,name TEXT NOT NULL,quantity INTEGER NOT NULL CHECK(quantity>0),unit_price_cents INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS inventory_movements(id INTEGER PRIMARY KEY,product_id TEXT NOT NULL,quantity INTEGER NOT NULL,reason TEXT NOT NULL,order_id INTEGER,actor_id INTEGER,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS returns(id INTEGER PRIMARY KEY,order_id INTEGER NOT NULL REFERENCES orders(id),user_id INTEGER NOT NULL REFERENCES users(id),reason TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'solicitada',created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY,actor_id INTEGER,action TEXT NOT NULL,entity TEXT NOT NULL,entity_id TEXT,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS coupons(code TEXT PRIMARY KEY,percent INTEGER NOT NULL,active INTEGER NOT NULL DEFAULT 1);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_returns_order ON returns(order_id);''')
  if c.execute('SELECT COUNT(*) FROM products').fetchone()[0]==0:
   for p in json.loads((ROOT/'backend'/'seed_products.json').read_text()):
    c.execute('INSERT INTO products(id,name,category,price_cents,discount,stock,metadata) VALUES(?,?,?,?,?,?,?)',(p['id'],p['name'],p['category'],round(p['price']*100),p.get('discount',0),p['stock'],json.dumps(p,ensure_ascii=False)))
  if c.execute('SELECT COUNT(*) FROM coupons').fetchone()[0]==0:c.execute('INSERT INTO coupons(code,percent) VALUES(?,?)',('STEP10',10))
  if c.execute('SELECT COUNT(*) FROM users WHERE role=?',('admin',)).fetchone()[0]==0:
   email=os.environ.get('STEPSTYLE_ADMIN_EMAIL');password=os.environ.get('STEPSTYLE_ADMIN_PASSWORD')
   if email and password and len(password)>=12:c.execute('INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)',('Administrador',email.lower(),pw_hash(password),'admin'))
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def user_for(handler):
 token=handler.headers.get('Authorization','').removeprefix('Bearer ').strip();sess=SESSIONS.get(token)
 if not sess or sess[1]<time.time():return None
 with db() as c:return c.execute('SELECT id,name,email,role FROM users WHERE id=?',(sess[0],)).fetchone()
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
 def reply(self,code,data):
  raw=json.dumps(data,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def body(self):
  size=int(self.headers.get('Content-Length','0'))
  if size>65536:raise ValueError('Solicitud demasiado grande')
  return json.loads(self.rfile.read(size)) if size else {}
 def require(self,admin=False):
  u=user_for(self)
  if not u:raise PermissionError('Inicia sesión')
  if admin and u['role']!='admin':raise PermissionError('Sin permisos')
  return u
 def do_GET(self):
  if not self.path.startswith('/api/'):
   if urlparse(self.path).path.startswith(('/backend/','/.git','/.env')):return self.send_error(403)
   return super().do_GET()
  try:
   path=urlparse(self.path).path;query=parse_qs(urlparse(self.path).query)
   with db() as c:
    if path=='/api/products':
     rows=c.execute('SELECT * FROM products WHERE active=1').fetchall();return self.reply(200,[dict(json.loads(x['metadata']),price=x['price_cents']/100,stock=x['stock'],discount=x['discount']) for x in rows])
    if path=='/api/me':
     u=self.require();return self.reply(200,dict(u))
    if path=='/api/orders':
     u=self.require();rows=c.execute('SELECT * FROM orders WHERE user_id=? ORDER BY id DESC',(u['id'],)).fetchall();return self.reply(200,[dict(x) for x in rows])
    if path=='/api/returns':
     u=self.require();rows=c.execute('SELECT * FROM returns WHERE user_id=? ORDER BY id DESC',(u['id'],)).fetchall();return self.reply(200,[dict(x) for x in rows])
    if path=='/api/admin/orders':
     self.require(True);return self.reply(200,[dict(x) for x in c.execute('SELECT * FROM orders ORDER BY id DESC')])
    if path=='/api/admin/products':
     self.require(True);return self.reply(200,[dict(x) for x in c.execute('SELECT id,name,category,price_cents,discount,stock,active FROM products ORDER BY id')])
    if path=='/api/admin/returns':
     self.require(True);return self.reply(200,[dict(x) for x in c.execute('SELECT * FROM returns ORDER BY id DESC')])
    if path=='/api/admin/reports':
     self.require(True);return self.reply(200,{'orders':c.execute('SELECT COUNT(*) FROM orders').fetchone()[0],'sales_cents':c.execute("SELECT COALESCE(SUM(total_cents),0) FROM orders WHERE status!='cancelado'").fetchone()[0],'low_stock':c.execute('SELECT COUNT(*) FROM products WHERE stock<=3 AND active=1').fetchone()[0],'returns':c.execute('SELECT COUNT(*) FROM returns').fetchone()[0]})
   return self.reply(404,{'error':'No encontrado'})
  except PermissionError as e:return self.reply(403,{'error':str(e)})
  except Exception as e:return self.reply(400,{'error':str(e)})
 def do_POST(self):return self.change('POST')
 def do_PATCH(self):return self.change('PATCH')
 def change(self,method):
  if not self.path.startswith('/api/'):return self.reply(404,{'error':'No encontrado'})
  try:
   path=urlparse(self.path).path;d=self.body()
   if path=='/api/auth/register':
    email=str(d.get('email','')).strip().lower();password=str(d.get('password',''))
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email) or len(password)<10 or len(str(d.get('name','')).strip())<2:raise ValueError('Revisa nombre, correo y contraseña (mínimo 10 caracteres)')
    with db() as c:
     try:c.execute('INSERT INTO users(name,email,password_hash) VALUES(?,?,?)',(str(d['name']).strip()[:100],email,pw_hash(password)))
     except sqlite3.IntegrityError:raise ValueError('El correo ya está registrado')
    return self.reply(201,{'ok':True})
   if path=='/api/auth/login':
    with db() as c:u=c.execute('SELECT * FROM users WHERE email=?',(str(d.get('email','')).lower(),)).fetchone()
    if not u or not verify(str(d.get('password','')),u['password_hash']):return self.reply(401,{'error':'Credenciales incorrectas'})
    token=secrets.token_urlsafe(32);SESSIONS[token]=(u['id'],time.time()+8*3600)
    return self.reply(200,{'token':token,'user':{'name':u['name'],'email':u['email'],'role':u['role']}})
   if path=='/api/auth/logout':
    SESSIONS.pop(self.headers.get('Authorization','').removeprefix('Bearer ').strip(),None);return self.reply(200,{'ok':True})
   u=self.require()
   if path=='/api/orders' and method=='POST':
    lines=d.get('items',[]);key=str(d.get('idempotency_key',''))
    if not isinstance(lines,list) or not 1<=len(lines)<=50 or len(key)<12 or not d.get('accept_terms'):raise ValueError('Pedido o aceptación inválidos')
    ship=d.get('shipping',{});required=['name','email','address','city','state','zip','phone']
    if not isinstance(ship,dict) or any(not str(ship.get(x,'')).strip() for x in required) or not re.fullmatch(r'\d{5}',str(ship.get('zip',''))):raise ValueError('Datos de entrega incompletos')
    if d.get('payment') not in ('Simulado','Transferencia','Tarjeta'):raise ValueError('Método de pago inválido')
    with LOCK:
     c=db()
     try:
      c.execute('BEGIN IMMEDIATE')
      old=c.execute('SELECT * FROM orders WHERE idempotency_key=? AND user_id=?',(key,u['id'])).fetchone()
      if old:c.rollback();return self.reply(200,{'folio':old['folio'],'total':old['total_cents']/100,'status':old['status']})
      subtotal=0;resolved=[];seen=set()
      for item in lines:
       pid=str(item.get('id',''));qty=int(item.get('quantity',0))
       if pid in seen:raise ValueError('Producto duplicado en carrito')
       seen.add(pid)
       if qty<1 or qty>99:raise ValueError('Cantidad inválida')
       p=c.execute('SELECT * FROM products WHERE id=? AND active=1',(pid,)).fetchone()
       if not p or p['stock']<qty:raise ValueError('Inventario insuficiente: '+pid)
       unit=(p['price_cents']*(100-p['discount'])+50)//100
       subtotal+=unit*qty;resolved.append((p,qty,unit))
      discount=0;coupon=str(d.get('coupon','')).upper()
      if coupon:
       cp=c.execute('SELECT percent FROM coupons WHERE code=? AND active=1',(coupon,)).fetchone()
       if not cp:raise ValueError('Cupón inválido')
       discount=(subtotal*cp['percent']+50)//100
      base=subtotal-discount;tax=(base*16+50)//100
      delivery=0 if subtotal>=250000 else 14900
      total=base+tax+delivery;folio='ST-'+secrets.token_hex(5).upper();ts=now()
      cur=c.execute('INSERT INTO orders(folio,user_id,created_at,shipping,subtotal_cents,tax_cents,shipping_cents,total_cents,coupon,terms_version,terms_accepted_at,idempotency_key) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(folio,u['id'],ts,json.dumps(ship,ensure_ascii=False),subtotal,tax,delivery,total,coupon,'1.0',ts,key));oid=cur.lastrowid
      for p,qty,unit in resolved:
       updated=c.execute('UPDATE products SET stock=stock-? WHERE id=? AND stock>=?', (qty,p['id'],qty))
       if updated.rowcount!=1:raise ValueError('Inventario insuficiente')
       c.execute('INSERT INTO order_items(order_id,product_id,sku,name,quantity,unit_price_cents) VALUES(?,?,?,?,?,?)',(oid,p['id'],p['id'],p['name'],qty,unit))
       c.execute('INSERT INTO inventory_movements(product_id,quantity,reason,order_id,actor_id,created_at) VALUES(?,?,?,?,?,?)',(p['id'],-qty,'venta',oid,u['id'],ts))
      c.execute('INSERT INTO audit_logs(actor_id,action,entity,entity_id,created_at) VALUES(?,?,?,?,?)',(u['id'],'crear','pedido',str(oid),ts));c.commit()
      return self.reply(201,{'folio':folio,'total':total/100,'subtotal':subtotal/100,'tax':tax/100,'shipping':delivery/100,'status':'pendiente','date':ts})
     except: c.rollback();raise
     finally:c.close()
   if path=='/api/returns' and method=='POST':
    oid=int(d.get('order_id',0));reason=str(d.get('reason','')).strip()[:500]
    if len(reason)<8:raise ValueError('Indica el motivo')
    with db() as c:
     order=c.execute('SELECT id FROM orders WHERE id=? AND user_id=?',(oid,u['id'])).fetchone()
     if not order:raise PermissionError('Pedido no disponible')
     cur=c.execute('INSERT INTO returns(order_id,user_id,reason,created_at) VALUES(?,?,?,?)',(oid,u['id'],reason,now()))
     return self.reply(201,{'id':cur.lastrowid,'status':'solicitada'})
   if path.startswith('/api/admin/'):
    self.require(True)
    with db() as c:
     if path=='/api/admin/products' and method=='POST':
      pid=str(d.get('id','')).strip();name=str(d.get('name','')).strip();cat=str(d.get('category','')).strip();price=int(d.get('price_cents',-1));stock=int(d.get('stock',-1))
      if not re.fullmatch(r'[A-Za-z0-9-]{2,24}',pid) or not name or not cat or price<0 or stock<0:raise ValueError('Producto inválido')
      meta={'id':pid,'name':name,'category':cat,'brand':'StepStyle','gender':'Unisex','style':'Casual','price':price/100,'discount':0,'stock':stock,'image':'','sizes':[25,26,27],'colors':['Negro'],'description':'','specs':[]}
      c.execute('INSERT INTO products(id,name,category,price_cents,stock,metadata) VALUES(?,?,?,?,?,?)',(pid,name,cat,price,stock,json.dumps(meta)))
      return self.reply(201,{'ok':True})
     m=re.fullmatch(r'/api/admin/products/([A-Za-z0-9-]+)',path)
     if m and method=='PATCH':
      pid=m.group(1);old=c.execute('SELECT * FROM products WHERE id=?',(pid,)).fetchone()
      if not old:raise ValueError('Producto inexistente')
      price=int(d.get('price_cents',old['price_cents']));stock=int(d.get('stock',old['stock']));active=int(d.get('active',old['active']))
      if price<0 or stock<0 or active not in (0,1):raise ValueError('Valores inválidos')
      c.execute('UPDATE products SET price_cents=?,stock=?,active=? WHERE id=?',(price,stock,active,pid))
      delta=stock-old['stock']
      if delta:c.execute('INSERT INTO inventory_movements(product_id,quantity,reason,actor_id,created_at) VALUES(?,?,?,?,?)',(pid,delta,'ajuste',u['id'],now()))
      c.execute('INSERT INTO audit_logs(actor_id,action,entity,entity_id,created_at) VALUES(?,?,?,?,?)',(u['id'],'editar','producto',pid,now()))
      return self.reply(200,{'ok':True})
     m=re.fullmatch(r'/api/admin/orders/(\d+)',path)
     if m and method=='PATCH':
      status=str(d.get('status',''));allowed={'pendiente':['preparando','cancelado'],'preparando':['enviado','cancelado'],'enviado':['entregado'],'entregado':[],'cancelado':[]}
      old=c.execute('SELECT status FROM orders WHERE id=?',(int(m.group(1)),)).fetchone()
      if not old or status not in allowed.get(old['status'],[]):raise ValueError('Transición de pedido no válida')
      c.execute('UPDATE orders SET status=? WHERE id=?',(status,int(m.group(1))))
      if status=='cancelado':
       for x in c.execute('SELECT product_id,quantity FROM order_items WHERE order_id=?',(int(m.group(1)),)):
        c.execute('UPDATE products SET stock=stock+? WHERE id=?',(x['quantity'],x['product_id']))
        c.execute('INSERT INTO inventory_movements(product_id,quantity,reason,order_id,actor_id,created_at) VALUES(?,?,?,?,?,?)',(x['product_id'],x['quantity'],'cancelación',int(m.group(1)),u['id'],now()))
      c.execute('INSERT INTO audit_logs(actor_id,action,entity,entity_id,created_at) VALUES(?,?,?,?,?)',(u['id'],'estado '+status,'pedido',m.group(1),now()))
      return self.reply(200,{'ok':True})
     m=re.fullmatch(r'/api/admin/returns/(\d+)',path)
     if m and method=='PATCH':
      status=str(d.get('status',''))
      if status not in ('aprobada','rechazada'):raise ValueError('Estado inválido')
      old=c.execute('SELECT status FROM returns WHERE id=?',(int(m.group(1)),)).fetchone()
      if not old or old['status']!='solicitada':raise ValueError('Solicitud no disponible')
      c.execute('UPDATE returns SET status=? WHERE id=?',(status,int(m.group(1))))
      c.execute('INSERT INTO audit_logs(actor_id,action,entity,entity_id,created_at) VALUES(?,?,?,?,?)',(u['id'],'resolver '+status,'devolución',m.group(1),now()))
      return self.reply(200,{'ok':True})
   return self.reply(404,{'error':'No encontrado'})
  except PermissionError as e:return self.reply(403,{'error':str(e)})
  except (ValueError,KeyError,TypeError,sqlite3.IntegrityError) as e:return self.reply(400,{'error':str(e)})
  except Exception as e:return self.reply(500,{'error':'Error interno'})
if __name__=='__main__':
 init();port=int(os.environ.get('PORT','8000'));print(f'StepStyle: http://127.0.0.1:{port}/');ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
