PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY, email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    nickname TEXT NOT NULL, password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('USER','ADMIN','INITIAL_ADMIN')),
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE','FROZEN','BANNED')),
    frozen_until REAL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
    purpose TEXT NOT NULL DEFAULT 'login', expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS email_challenges (
    id INTEGER PRIMARY KEY, email TEXT NOT NULL, purpose TEXT NOT NULL,
    code_hash TEXT NOT NULL, expires_at REAL NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
    used INTEGER NOT NULL DEFAULT 0, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS media (
    key TEXT PRIMARY KEY, owner_id INTEGER NOT NULL REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY, seller_id INTEGER NOT NULL REFERENCES users(id),
    status TEXT NOT NULL DEFAULT 'DRAFT' CHECK(status IN
      ('DRAFT','PENDING_REVIEW','REJECTED','PUBLISHED','RESERVED','OFFLINE','SOLD','VIOLATION_BANNED')),
    current_version_id INTEGER REFERENCES product_versions(id),
    approved_version_id INTEGER REFERENCES product_versions(id),
    revision INTEGER NOT NULL DEFAULT 1, published_at REAL, deleted_at REAL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS product_versions (
    id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id),
    version_no INTEGER NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL,
    category_id INTEGER REFERENCES categories(id), price_cents INTEGER NOT NULL CHECK(price_cents>=0),
    condition TEXT NOT NULL, location TEXT NOT NULL, note TEXT NOT NULL,
    image_keys TEXT NOT NULL DEFAULT '[]', created_at REAL NOT NULL,
    UNIQUE(product_id, version_no)
);
CREATE TABLE IF NOT EXISTS review_records (
    id INTEGER PRIMARY KEY, version_id INTEGER UNIQUE NOT NULL REFERENCES product_versions(id),
    reviewer_id INTEGER NOT NULL REFERENCES users(id), conclusion TEXT NOT NULL,
    opinion TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id),
    buyer_id INTEGER NOT NULL REFERENCES users(id), status TEXT NOT NULL
      CHECK(status IN ('LOCKED','SELLER_CONFIRMED','CANCELLED','COMPLETED','TERMINATED')),
    accepted_price INTEGER NOT NULL, accepted_version_id INTEGER REFERENCES product_versions(id),
    seller_accepted_at REAL, buyer_trade_confirmed_at REAL, seller_trade_confirmed_at REAL,
    confirmation_version_id INTEGER REFERENCES product_versions(id), created_at REAL NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_reservation ON reservations(product_id)
    WHERE status IN ('LOCKED','SELLER_CONFIRMED');
CREATE TABLE IF NOT EXISTS waitlists (
    id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id),
    buyer_id INTEGER NOT NULL REFERENCES users(id), status TEXT NOT NULL
      CHECK(status IN ('WAITING','PROMOTED','CANCELLED','TERMINATED')), joined_at REAL NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS one_waiting_buyer ON waitlists(product_id,buyer_id)
    WHERE status='WAITING';
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY, product_id INTEGER UNIQUE NOT NULL REFERENCES products(id),
    reservation_id INTEGER UNIQUE NOT NULL REFERENCES reservations(id),
    buyer_id INTEGER NOT NULL REFERENCES users(id), seller_id INTEGER NOT NULL REFERENCES users(id),
    version_id INTEGER NOT NULL REFERENCES product_versions(id), price_cents INTEGER NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id), completed_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
    product_id INTEGER NOT NULL REFERENCES products(id), reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING', result TEXT NOT NULL DEFAULT '', created_at REAL NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS one_pending_complaint ON complaints(user_id,product_id)
    WHERE status='PENDING';
CREATE TABLE IF NOT EXISTS moderation_actions (
    id INTEGER PRIMARY KEY, admin_id INTEGER NOT NULL REFERENCES users(id),
    target_type TEXT NOT NULL, target_id INTEGER NOT NULL, owner_id INTEGER NOT NULL REFERENCES users(id),
    action TEXT NOT NULL, reason TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS appeals (
    id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
    moderation_id INTEGER NOT NULL REFERENCES moderation_actions(id), content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'SUBMITTED', result TEXT NOT NULL DEFAULT '', created_at REAL NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS one_pending_appeal ON appeals(user_id,moderation_id)
    WHERE status='SUBMITTED';
CREATE TABLE IF NOT EXISTS reservation_messages (
    id INTEGER PRIMARY KEY, reservation_id INTEGER NOT NULL REFERENCES reservations(id),
    sender_id INTEGER NOT NULL REFERENCES users(id), content TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS operation_logs (
    id INTEGER PRIMARY KEY, actor_id INTEGER REFERENCES users(id), action TEXT NOT NULL,
    target_type TEXT NOT NULL, target_id INTEGER, before_state TEXT NOT NULL DEFAULT '',
    after_state TEXT NOT NULL DEFAULT '', result TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS request_receipts (
    actor_id INTEGER NOT NULL REFERENCES users(id), action TEXT NOT NULL,
    request_key TEXT NOT NULL, result_id INTEGER NOT NULL, PRIMARY KEY(actor_id,action,request_key)
);
CREATE INDEX IF NOT EXISTS product_status ON products(status,deleted_at);
CREATE INDEX IF NOT EXISTS log_time ON operation_logs(created_at);
CREATE INDEX IF NOT EXISTS reservation_buyer ON reservations(buyer_id);
INSERT OR IGNORE INTO categories(id,name) VALUES
    (1,'数码电子'),(2,'教材书籍'),(3,'生活用品'),(4,'运动户外'),(5,'其他');
PRAGMA user_version = 1;
