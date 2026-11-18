-- StepStyle · Migración 001 · Esquema inicial PostgreSQL
-- Importes en centavos (enteros) para evitar errores de redondeo.

CREATE TABLE IF NOT EXISTS users(
  id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name          VARCHAR(100) NOT NULL,
  email         VARCHAR(254) NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role          VARCHAR(20) NOT NULL DEFAULT 'customer' CHECK (role IN ('customer','admin')),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sessions(
  token_hash  CHAR(64) PRIMARY KEY,
  user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at  TIMESTAMPTZ NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

CREATE TABLE IF NOT EXISTS products(
  id           VARCHAR(24) PRIMARY KEY,               -- SKU
  name         VARCHAR(150) NOT NULL,
  category     VARCHAR(50) NOT NULL,
  price_cents  INTEGER NOT NULL CHECK (price_cents >= 0),
  discount     INTEGER NOT NULL DEFAULT 0 CHECK (discount BETWEEN 0 AND 100),
  stock        INTEGER NOT NULL CHECK (stock >= 0),
  active       SMALLINT NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
  metadata     JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);

CREATE TABLE IF NOT EXISTS coupons(
  code     VARCHAR(30) PRIMARY KEY,
  percent  INTEGER NOT NULL CHECK (percent BETWEEN 1 AND 100),
  active   SMALLINT NOT NULL DEFAULT 1 CHECK (active IN (0,1))
);

CREATE TABLE IF NOT EXISTS orders(
  id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  folio              VARCHAR(20) NOT NULL UNIQUE,
  user_id            BIGINT NOT NULL REFERENCES users(id),
  created_at         TIMESTAMPTZ NOT NULL,
  shipping           TEXT NOT NULL,                  -- JSON con datos de entrega
  subtotal_cents     INTEGER NOT NULL,
  tax_cents          INTEGER NOT NULL,
  shipping_cents     INTEGER NOT NULL,
  total_cents        INTEGER NOT NULL,
  status             VARCHAR(20) NOT NULL DEFAULT 'pendiente'
                     CHECK (status IN ('pendiente','preparando','enviado','entregado','cancelado')),
  payment_status     VARCHAR(20) NOT NULL DEFAULT 'aprobado',
  coupon             VARCHAR(30),
  terms_version      VARCHAR(10) NOT NULL,
  terms_accepted_at  TIMESTAMPTZ NOT NULL,
  idempotency_key    VARCHAR(100) NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);

CREATE TABLE IF NOT EXISTS order_items(
  id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  order_id          BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  product_id        VARCHAR(24) NOT NULL REFERENCES products(id),
  sku               VARCHAR(24) NOT NULL,
  name              VARCHAR(150) NOT NULL,
  quantity          INTEGER NOT NULL CHECK (quantity > 0),
  unit_price_cents  INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);

CREATE TABLE IF NOT EXISTS inventory_movements(
  id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  product_id  VARCHAR(24) NOT NULL REFERENCES products(id),
  quantity    INTEGER NOT NULL,
  reason      VARCHAR(50) NOT NULL,
  order_id    BIGINT REFERENCES orders(id),
  actor_id    BIGINT REFERENCES users(id),
  created_at  TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory_movements(product_id);

CREATE TABLE IF NOT EXISTS returns(
  id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  order_id    BIGINT NOT NULL REFERENCES orders(id),
  user_id     BIGINT NOT NULL REFERENCES users(id),
  reason      VARCHAR(500) NOT NULL,
  status      VARCHAR(20) NOT NULL DEFAULT 'solicitada' CHECK (status IN ('solicitada','aprobada','rechazada')),
  created_at  TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_returns_order ON returns(order_id);

CREATE TABLE IF NOT EXISTS audit_logs(
  id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  actor_id    BIGINT REFERENCES users(id),
  action      VARCHAR(50) NOT NULL,
  entity      VARCHAR(50) NOT NULL,
  entity_id   VARCHAR(50),
  created_at  TIMESTAMPTZ NOT NULL
);
