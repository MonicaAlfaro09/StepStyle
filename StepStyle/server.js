require("dotenv").config();
const express = require("express");
const session = require("express-session");
const SQLiteStore = require("connect-sqlite3")(session);
const Database = require("better-sqlite3");
const bcrypt = require("bcryptjs");
const helmet = require("helmet");
const rateLimit = require("express-rate-limit");
const path = require("path");
const fs = require("fs");

const app = express();
const PORT = Number(process.env.PORT || 3000);
const DB_FILE = process.env.DB_FILE || path.join(__dirname, "data", "stepstyle.sqlite");
fs.mkdirSync(path.dirname(DB_FILE), { recursive: true });
const db = new Database(DB_FILE);
db.pragma("journal_mode = WAL");
db.pragma("foreign_keys = ON");

db.exec(`
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'customer' CHECK(role IN ('customer','admin')),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS products (
 id TEXT PRIMARY KEY, brand TEXT NOT NULL, name TEXT NOT NULL, gender TEXT, style TEXT,
 category TEXT NOT NULL, price REAL NOT NULL CHECK(price >= 0), discount REAL NOT NULL DEFAULT 0,
 stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0), image TEXT, description TEXT, active INTEGER NOT NULL DEFAULT 1,
 sizes_json TEXT NOT NULL DEFAULT '[]', colors_json TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS orders (
 id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT NOT NULL UNIQUE, user_id INTEGER NOT NULL REFERENCES users(id),
 customer_name TEXT NOT NULL, email TEXT NOT NULL, address TEXT NOT NULL, city TEXT NOT NULL, state TEXT NOT NULL,
 zip TEXT NOT NULL, phone TEXT NOT NULL, payment_method TEXT NOT NULL, payment_status TEXT NOT NULL DEFAULT 'approved',
 status TEXT NOT NULL DEFAULT 'pagado', subtotal REAL NOT NULL, discount REAL NOT NULL, shipping REAL NOT NULL,
 tax REAL NOT NULL, total REAL NOT NULL, accepted_terms INTEGER NOT NULL, terms_version TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS order_items (
 id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
 product_id TEXT NOT NULL, sku TEXT NOT NULL, product_name TEXT NOT NULL, size TEXT, color TEXT,
 quantity INTEGER NOT NULL, unit_price REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS inventory_movements (
 id INTEGER PRIMARY KEY AUTOINCREMENT, product_id TEXT NOT NULL REFERENCES products(id),
 movement_type TEXT NOT NULL, quantity INTEGER NOT NULL, reason TEXT NOT NULL,
 user_id INTEGER REFERENCES users(id), order_id INTEGER REFERENCES orders(id), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS return_requests (
 id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL REFERENCES orders(id),
 user_id INTEGER NOT NULL REFERENCES users(id), reason TEXT NOT NULL, details TEXT,
 status TEXT NOT NULL DEFAULT 'recibida', resolution TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS audit_logs (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT NOT NULL, entity TEXT NOT NULL,
 entity_id TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
`);

const catalog = JSON.parse(fs.readFileSync(path.join(__dirname, "data_products.json"), "utf8"));
const addProduct = db.prepare(`INSERT OR IGNORE INTO products
(id,brand,name,gender,style,category,price,discount,stock,image,description,sizes_json,colors_json)
VALUES (@id,@brand,@name,@gender,@style,@category,@price,@discount,@stock,@image,@description,@sizes,@colors)`);
const seed = db.transaction(() => catalog.forEach(p => addProduct.run({...p, sizes:JSON.stringify(p.sizes||[]), colors:JSON.stringify(p.colors||[])})));
seed();

const countAdmin = db.prepare("SELECT COUNT(*) n FROM users WHERE role='admin'").get().n;
if (!countAdmin) {
 const email=(process.env.ADMIN_EMAIL || "admin@stepstyle.mx").toLowerCase();
 const password=process.env.ADMIN_PASSWORD || "AdminStepStyle2026!";
 db.prepare("INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,'admin')")
   .run("Administrador StepStyle", email, bcrypt.hashSync(password, 12));
 console.warn("Cuenta administrativa inicial creada. Cambia ADMIN_PASSWORD antes de publicar en producción.");
}

app.disable("x-powered-by");
if (process.env.NODE_ENV === "production") app.set("trust proxy", 1);
app.use(helmet({ contentSecurityPolicy:false }));
app.use(express.json({limit:"100kb"}));
app.use(rateLimit({windowMs:15*60*1000, limit:300, standardHeaders:true, legacyHeaders:false}));
app.use(session({
 secret: process.env.SESSION_SECRET || "CAMBIAR-ESTE-SECRETO-LARGO-ANTES-DE-PRODUCCION",
 resave:false, saveUninitialized:false,
 store:new SQLiteStore({db:"sessions.sqlite", dir:path.dirname(DB_FILE)}),
 cookie:{httpOnly:true, sameSite:"lax", secure:process.env.NODE_ENV==="production", maxAge:8*60*60*1000}
}));
app.use(express.static(__dirname));

const q = (sql,...args)=>db.prepare(sql).all(...args);
const one=(sql,...args)=>db.prepare(sql).get(...args);
const audit=(req,action,entity,id)=>db.prepare("INSERT INTO audit_logs(user_id,action,entity,entity_id) VALUES(?,?,?,?)").run(req.session.user?.id||null,action,entity,String(id??""));
const safeUser=u=>({id:u.id,name:u.name,email:u.email,role:u.role});
const requireAuth=(req,res,next)=>req.session.user?next():res.status(401).json({error:"Inicia sesión para continuar."});
const requireAdmin=(req,res,next)=>req.session.user?.role==="admin"?next():res.status(403).json({error:"Acceso exclusivo para administración."});
const publicProduct=p=>({...p,sizes:JSON.parse(p.sizes_json),colors:JSON.parse(p.colors_json),discounted_price:Math.round(p.price*(1-p.discount/100)*100)/100});

app.get("/api/health",(req,res)=>res.json({status:"ok",service:"StepStyle API",database:"connected"}));
app.post("/api/auth/register",rateLimit({windowMs:60*60*1000,limit:10}), (req,res)=>{
 const {name,email,password}=req.body||{};
 if(!name||!email||!password||String(name).length>100||!/^\S+@\S+\.\S+$/.test(email)||String(password).length<10)
  return res.status(400).json({error:"Proporciona nombre, correo válido y contraseña de al menos 10 caracteres."});
 try{
  const info=db.prepare("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)").run(String(name).trim(),String(email).trim().toLowerCase(),bcrypt.hashSync(password,12));
  req.session.user=safeUser(one("SELECT * FROM users WHERE id=?",info.lastInsertRowid));
  res.status(201).json({user:req.session.user});
 }catch(e){res.status(409).json({error:"Ese correo ya está registrado."});}
});
app.post("/api/auth/login",rateLimit({windowMs:15*60*1000,limit:12}), (req,res)=>{
 const u=one("SELECT * FROM users WHERE email=?",String(req.body?.email||"").trim().toLowerCase());
 if(!u||!bcrypt.compareSync(String(req.body?.password||""),u.password_hash))return res.status(401).json({error:"Correo o contraseña incorrectos."});
 req.session.regenerate(err=>{if(err)return res.status(500).json({error:"No fue posible iniciar sesión."});req.session.user=safeUser(u);res.json({user:req.session.user});});
});
app.post("/api/auth/logout",requireAuth,(req,res)=>req.session.destroy(()=>res.json({ok:true})));
app.get("/api/auth/me",(req,res)=>res.json({user:req.session.user||null}));

app.get("/api/products",(req,res)=>res.json(q("SELECT * FROM products WHERE active=1 ORDER BY id").map(publicProduct)));
app.get("/api/products/:id",(req,res)=>{const p=one("SELECT * FROM products WHERE id=? AND active=1",req.params.id);p?res.json(publicProduct(p)):res.status(404).json({error:"Producto no encontrado."});});

app.post("/api/orders",requireAuth,(req,res)=>{
 const {items,customer,paymentMethod,acceptedTerms,shipping}=req.body||{};
 if(!Array.isArray(items)||!items.length||items.length>30)return res.status(400).json({error:"El carrito no es válido."});
 if(!customer||!customer.name||!customer.email||!customer.address||!customer.city||!customer.state||!/^\d{5}$/.test(customer.zip||"")||!customer.phone)
  return res.status(400).json({error:"Completa los datos de entrega."});
 if(acceptedTerms!==true)return res.status(400).json({error:"Debes aceptar términos y aviso de privacidad."});
 if(!["Simulación aprobada","Transferencia simulada"].includes(paymentMethod))return res.status(400).json({error:"Método de pago de demostración no válido."});
 const create=db.transaction(()=>{
  let subtotal=0, lines=[];
  for(const item of items){
   const p=one("SELECT * FROM products WHERE id=? AND active=1",String(item.id));
   const qty=Number(item.quantity);
   if(!p||!Number.isInteger(qty)||qty<1)throw new Error("Producto o cantidad inválida.");
   if(p.stock<qty)throw new Error(`Stock insuficiente para ${p.name}. Disponible: ${p.stock}.`);
   const unit=Math.round(p.price*(1-p.discount/100)*100)/100;
   subtotal+=unit*qty;lines.push({p,qty,unit,size:String(item.size||""),color:String(item.color||"")});
  }
  const discount=0, taxable=subtotal-discount, tax=Math.round(taxable*.16*100)/100;
  const zip=String(customer.zip);
  const ship=subtotal>=2500?0:(Number(zip)>=88000&&Number(zip)<=88999?99:169);
  const total=Math.round((taxable+tax+ship)*100)/100;
  const number="ST-"+Date.now().toString().slice(-8)+"-"+Math.floor(100+Math.random()*900);
  const info=db.prepare(`INSERT INTO orders(number,user_id,customer_name,email,address,city,state,zip,phone,payment_method,subtotal,discount,shipping,tax,total,accepted_terms,terms_version)
  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`).run(number,req.session.user.id,String(customer.name),String(customer.email),String(customer.address),String(customer.city),String(customer.state),String(customer.zip),String(customer.phone),paymentMethod,subtotal,discount,ship,tax,total,1,"2026-11-17-v1");
  const orderId=info.lastInsertRowid;
  for(const l of lines){
   db.prepare("INSERT INTO order_items(order_id,product_id,sku,product_name,size,color,quantity,unit_price) VALUES(?,?,?,?,?,?,?,?)")
    .run(orderId,l.p.id,l.p.id,l.p.name,l.size,l.color,l.qty,l.unit);
   db.prepare("UPDATE products SET stock=stock-? WHERE id=?").run(l.qty,l.p.id);
   db.prepare("INSERT INTO inventory_movements(product_id,movement_type,quantity,reason,user_id,order_id) VALUES(?,?,?,?,?,?)")
    .run(l.p.id,"salida",l.qty,"Venta "+number,req.session.user.id,orderId);
  }
  audit(req,"crear_pedido","orders",orderId);
  return {id:orderId,number,total,subtotal,tax,shipping:ship,status:"pagado"};
 });
 try{res.status(201).json({order:create()});}catch(e){res.status(409).json({error:e.message});}
});
app.get("/api/orders/mine",requireAuth,(req,res)=>{
 const orders=q("SELECT id,number,status,total,created_at FROM orders WHERE user_id=? ORDER BY id DESC",req.session.user.id);
 res.json(orders);
});
app.get("/api/orders/:id",requireAuth,(req,res)=>{
 const o=one("SELECT * FROM orders WHERE id=? AND (user_id=? OR ?='admin')",Number(req.params.id),req.session.user.id,req.session.user.role);
 if(!o)return res.status(404).json({error:"Pedido no encontrado."});
 res.json({order:o,items:q("SELECT * FROM order_items WHERE order_id=?",o.id)});
});
app.get("/api/returns/mine",requireAuth,(req,res)=>res.json(q("SELECT r.id,r.reason,r.status,r.resolution,r.created_at,o.number FROM return_requests r JOIN orders o ON o.id=r.order_id WHERE r.user_id=? ORDER BY r.id DESC",req.session.user.id)));
app.post("/api/returns",requireAuth,(req,res)=>{
 const {orderId,reason,details}=req.body||{};
 const o=one("SELECT id FROM orders WHERE id=? AND user_id=?",Number(orderId),req.session.user.id);
 if(!o||!reason)return res.status(400).json({error:"Pedido o motivo no válido."});
 const info=db.prepare("INSERT INTO return_requests(order_id,user_id,reason,details) VALUES(?,?,?,?)").run(o.id,req.session.user.id,String(reason),String(details||""));
 audit(req,"solicitar_devolucion","return_requests",info.lastInsertRowid);
 res.status(201).json({id:info.lastInsertRowid,status:"recibida"});
});

app.use("/api/admin",requireAuth,requireAdmin);
app.get("/api/admin/summary",(req,res)=>res.json({
 products:one("SELECT COUNT(*) n FROM products WHERE active=1").n,
 orders:one("SELECT COUNT(*) n FROM orders").n,
 revenue:one("SELECT COALESCE(SUM(total),0) n FROM orders WHERE payment_status='approved'").n,
 lowStock:q("SELECT id,name,stock FROM products WHERE active=1 AND stock<=3 ORDER BY stock")
}));
app.get("/api/admin/products",(req,res)=>res.json(q("SELECT * FROM products ORDER BY id").map(publicProduct)));
app.post("/api/admin/products",(req,res)=>{
 const p=req.body||{};if(!p.id||!p.name||!p.category||!Number.isFinite(Number(p.price))||Number(p.price)<0)return res.status(400).json({error:"ID, nombre, categoría y precio son obligatorios."});
 try{db.prepare(`INSERT INTO products(id,brand,name,gender,style,category,price,discount,stock,image,description,sizes_json,colors_json)
 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)`).run(p.id,p.brand||"StepStyle",p.name,p.gender||"Unisex",p.style||"Casual",p.category,Number(p.price),Number(p.discount)||0,Math.max(0,Number(p.stock)||0),p.image||"",p.description||"",JSON.stringify(p.sizes||[]),JSON.stringify(p.colors||[]));audit(req,"crear","products",p.id);res.status(201).json({ok:true});}
 catch(e){res.status(409).json({error:"No se pudo crear. Verifica que el SKU no exista."});}
});
app.patch("/api/admin/products/:id",(req,res)=>{
 const p=req.body||{};const current=one("SELECT * FROM products WHERE id=?",req.params.id);if(!current)return res.status(404).json({error:"Producto no encontrado."});
 const nextStock=Math.max(0,Number(p.stock??current.stock));
 db.prepare(`UPDATE products SET name=?,brand=?,category=?,price=?,discount=?,stock=?,description=?,active=? WHERE id=?`)
 .run(p.name??current.name,p.brand??current.brand,p.category??current.category,Number(p.price??current.price),Number(p.discount??current.discount),nextStock,p.description??current.description,p.active===false?0:1,req.params.id);
 if(nextStock!==current.stock)db.prepare("INSERT INTO inventory_movements(product_id,movement_type,quantity,reason,user_id) VALUES(?,?,?,?,?)")
  .run(req.params.id,"ajuste",Math.abs(nextStock-current.stock),"Ajuste manual de inventario",req.session.user.id);
 audit(req,"actualizar","products",req.params.id);res.json({ok:true});
});
app.delete("/api/admin/products/:id",(req,res)=>{db.prepare("UPDATE products SET active=0 WHERE id=?").run(req.params.id);audit(req,"baja_logica","products",req.params.id);res.json({ok:true});});
app.get("/api/admin/orders",(req,res)=>res.json(q("SELECT id,number,customer_name,email,status,total,created_at FROM orders ORDER BY id DESC")));
app.patch("/api/admin/orders/:id",(req,res)=>{
 const allowed=["pagado","preparando","enviado","entregado","cancelado","reembolsado"],status=req.body?.status;
 if(!allowed.includes(status))return res.status(400).json({error:"Estado no permitido."});
 const change=db.transaction(()=>{
 const order=one("SELECT * FROM orders WHERE id=?",Number(req.params.id));if(!order)return false;
 if(status==="cancelado"&&order.status!=="cancelado"&&order.status!=="reembolsado"){
  const lines=q("SELECT * FROM order_items WHERE order_id=?",order.id);
  for(const line of lines){db.prepare("UPDATE products SET stock=stock+? WHERE id=?").run(line.quantity,line.product_id);
   db.prepare("INSERT INTO inventory_movements(product_id,movement_type,quantity,reason,user_id,order_id) VALUES(?,?,?,?,?,?)").run(line.product_id,"entrada",line.quantity,"Cancelación "+order.number,req.session.user.id,order.id);}
 }
 db.prepare("UPDATE orders SET status=? WHERE id=?").run(status,order.id);audit(req,"cambiar_estado","orders",req.params.id);return true;
 });
 if(!change())return res.status(404).json({error:"Pedido no encontrado."});res.json({ok:true});
});
app.get("/api/admin/returns",(req,res)=>res.json(q("SELECT r.*,o.number,u.email FROM return_requests r JOIN orders o ON o.id=r.order_id JOIN users u ON u.id=r.user_id ORDER BY r.id DESC")));
app.patch("/api/admin/returns/:id",(req,res)=>{
 const {status,resolution}=req.body||{};if(!["en_revision","autorizada","rechazada","resuelta"].includes(status))return res.status(400).json({error:"Estado no válido."});
 db.prepare("UPDATE return_requests SET status=?,resolution=? WHERE id=?").run(status,String(resolution||""),Number(req.params.id));audit(req,"resolver_devolucion","return_requests",req.params.id);res.json({ok:true});
});
app.get("/api/admin/audit",(req,res)=>res.json(q("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 200")));

app.get("*",(req,res)=>res.sendFile(path.join(__dirname,"index.html")));
app.listen(PORT,()=>console.log(`StepStyle disponible en http://localhost:${PORT}`));
