"""SQLite 仓储与事务边界；每次操作独立连接。"""

import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from .domain import BusinessError, principal, require


class Database:
    def __init__(self, path):
        self.path = Path(path)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")
        try:
            yield connection
        finally:
            connection.close()

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript(Path(__file__).with_name("schema.sql").read_text())

    def rows(self, sql, params=()):
        with self.connect() as db:
            return [dict(row) for row in db.execute(sql, params)]

    def one(self, sql, params=()):
        rows = self.rows(sql, params)
        return rows[0] if rows else None

    @contextmanager
    def transaction(self, actor_id, action, target_type="system", target_id=None):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                log(db, actor_id, action, target_type, target_id, "SUCCESS")
                db.commit()
            except (BusinessError, sqlite3.IntegrityError) as exc:
                db.rollback()
                db.execute("BEGIN IMMEDIATE")
                log(db, actor_id, action, target_type, target_id, "DENIED")
                db.commit()
                if isinstance(exc, sqlite3.IntegrityError):
                    raise BusinessError("记录重复或状态已变化，请刷新后重试") from exc
                raise
            except Exception:
                db.rollback()
                raise


def log(db, actor_id, action, target_type, target_id, result, before="", after=""):
    db.execute(
        "INSERT INTO operation_logs(actor_id,action,target_type,target_id,result,"
        "before_state,after_state,created_at) VALUES(?,?,?,?,?,?,?,?)",
        (actor_id, action, target_type, target_id, result, before, after, time.time()),
    )


def active_user(db, user_id, admin=False, ordinary=False):
    row = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    require(row is not None, "请先登录", 401)
    expired = row["status"] == "FROZEN" and row["frozen_until"] is not None
    if expired and row["frozen_until"] <= time.time():
        db.execute("UPDATE users SET status='ACTIVE',frozen_until=NULL WHERE id=?", (user_id,))
        db.execute(
            "UPDATE moderation_actions SET active=0 WHERE target_type='user' AND "
            "target_id=? AND active=1",
            (user_id,),
        )
        log(db, user_id, "FREEZE_EXPIRED", "user", user_id, "SUCCESS", "FROZEN", "ACTIVE")
        row = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    require(row["status"] == "ACTIVE", "账户受限，请通过申诉入口联系管理员", 403)
    user = principal(row)
    require(not admin or user.is_admin, "需要管理员权限", 403)
    require(not ordinary or user.role == "USER", "该操作仅供普通用户使用", 403)
    return user


def receipt(db, actor, action, key):
    require(isinstance(key, str) and 8 <= len(key) <= 100, "请求标识无效，请刷新", 400)
    row = db.execute(
        "SELECT result_id FROM request_receipts WHERE actor_id=? AND action=? AND request_key=?",
        (actor, action, key),
    ).fetchone()
    return row[0] if row else None


def remember(db, actor, action, key, result):
    db.execute("INSERT INTO request_receipts VALUES(?,?,?,?)", (actor, action, key, result))
