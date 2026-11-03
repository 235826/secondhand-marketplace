"""学校邮箱验证、账户、服务端会话与最小权限授权。"""

import hashlib
import hmac
import json
import secrets
import smtplib
import time
from email.message import EmailMessage
from pathlib import Path

from .domain import require, text
from .storage import active_user, log


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def password_hash(password):
    require(
        isinstance(password, str) and 10 <= len(password) <= 128, "密码需为 10～128 个字符", 400
    )
    salt = secrets.token_hex(16)
    derived = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1)
    return f"scrypt${salt}${derived.hex()}"


def password_matches(password, encoded):
    try:
        method, salt, expected = encoded.split("$")
        if method != "scrypt" or len(password) > 128:
            return False
        result = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1)
        return hmac.compare_digest(result.hex(), expected)
    except (ValueError, AttributeError):
        return False


class EmailService:
    """开发 outbox 不公开提供 HTTP 读取入口；SMTP 配置时真实发送。"""

    def __init__(self, outbox, smtp=None):
        self.outbox = Path(outbox)
        self.smtp = smtp

    def send(self, email, purpose, code):
        if self.smtp:
            message = EmailMessage()
            message["From"] = self.smtp["sender"]
            message["To"] = email
            message["Subject"] = "校园二手交易验证码"
            message.set_content(f"用途：{purpose}。验证码：{code}，10 分钟有效。")
            with smtplib.SMTP_SSL(self.smtp["host"], self.smtp.get("port", 465)) as server:
                server.login(self.smtp["username"], self.smtp["password"])
                server.send_message(message)
        else:
            self.outbox.mkdir(parents=True, exist_ok=True)
            path = self.outbox / f"{secrets.token_hex(16)}.json"
            path.write_text(
                json.dumps({"email": email, "purpose": purpose, "code": code}, ensure_ascii=False)
            )
            path.chmod(0o600)


class AccountService:
    def __init__(self, database, email_service, domains=("nju.edu.cn", "smail.nju.edu.cn")):
        self.db = database
        self.email_service = email_service
        self.domains = domains
        self.dummy_hash = password_hash(secrets.token_urlsafe(24))

    def normalize_email(self, email):
        email = text(email, "学校邮箱", 254).lower()
        local, separator, domain = email.partition("@")
        require(
            separator and local and domain in self.domains and "@" not in domain,
            "请使用受支持的学校邮箱",
            400,
        )
        return email

    def send_code(self, email, purpose):
        email = self.normalize_email(email)
        require(purpose in {"register", "reset", "appeal"}, "验证码用途无效", 400)
        code = f"{secrets.randbelow(1000000):06d}"
        now = time.time()
        with self.db.transaction(None, "EMAIL_CHALLENGE") as db:
            recent = db.execute(
                "SELECT created_at FROM email_challenges WHERE email=? ORDER BY id DESC LIMIT 1",
                (email,),
            ).fetchone()
            require(not recent or now - recent[0] >= 60, "请稍后再获取验证码", 429)
            db.execute(
                "UPDATE email_challenges SET used=1 WHERE email=? AND purpose=?", (email, purpose)
            )
            db.execute(
                "INSERT INTO email_challenges(email,purpose,code_hash,expires_at,created_at) "
                "VALUES(?,?,?,?,?)",
                (email, purpose, digest(code), now + 600, now),
            )
            self.email_service.send(email, purpose, code)

    def verify_code(self, email, purpose, code):
        # 错误次数单独提交，避免注册事务回滚后无限尝试验证码。
        with self.db.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM email_challenges WHERE email=? AND purpose=? "
                "ORDER BY id DESC LIMIT 1",
                (email, purpose),
            ).fetchone()
            valid = row and not row["used"] and row["expires_at"] > time.time()
            valid = valid and row["attempts"] < 5
            if row:
                db.execute(
                    "UPDATE email_challenges SET attempts=attempts+1 WHERE id=?", (row["id"],)
                )
            valid = valid and hmac.compare_digest(row["code_hash"], digest(str(code)))
            if valid:
                db.execute("UPDATE email_challenges SET used=1 WHERE id=?", (row["id"],))
            log(db, None, "VERIFY_EMAIL", "system", None, "SUCCESS" if valid else "DENIED")
            db.commit()
        require(valid, "验证码错误、已使用或已过期", 400)

    def register(self, email, nickname, password, code):
        email = self.normalize_email(email)
        nickname = text(nickname, "昵称", 30)
        encoded = password_hash(password)
        self.verify_code(email, "register", code)
        with self.db.transaction(None, "REGISTER", "user") as db:
            return db.execute(
                "INSERT INTO users(email,nickname,password_hash,role,created_at) "
                "VALUES(?,?,?,'USER',?)",
                (email, nickname, encoded, time.time()),
            ).lastrowid

    def bootstrap(self, email, password):
        email = self.normalize_email(email)
        encoded = password_hash(password)
        with self.db.transaction(None, "BOOTSTRAP", "user") as db:
            require(
                not db.execute("SELECT 1 FROM users WHERE role='INITIAL_ADMIN'").fetchone(),
                "初始管理员已存在",
            )
            return db.execute(
                "INSERT INTO users(email,nickname,password_hash,role,created_at) "
                "VALUES(?,? ,?,'INITIAL_ADMIN',?)",
                (email, "初始管理员", encoded, time.time()),
            ).lastrowid

    def create_admin(self, actor, email, nickname, password):
        email = self.normalize_email(email)
        encoded = password_hash(password)
        with self.db.transaction(actor, "CREATE_ADMIN", "user") as db:
            user = active_user(db, actor, admin=True)
            require(user.role == "INITIAL_ADMIN", "仅初始管理员可创建管理员", 403)
            return db.execute(
                "INSERT INTO users(email,nickname,password_hash,role,created_at) "
                "VALUES(?,?,?,'ADMIN',?)",
                (email, text(nickname, "昵称", 30), encoded, time.time()),
            ).lastrowid

    def login(self, email, password):
        email = str(email).strip().lower()
        with self.db.transaction(None, "LOGIN", "user") as db:
            row = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            matches = password_matches(password, row["password_hash"] if row else self.dummy_hash)
            require(row and matches, "账号或密码错误", 401)
            active_user(db, row["id"])
            token = secrets.token_urlsafe(32)
            db.execute(
                "INSERT INTO sessions VALUES(?,?,'login',?)",
                (digest(token), row["id"], time.time() + 28800),
            )
            log(db, row["id"], "AUTHENTICATED", "user", row["id"], "SUCCESS")
            return token

    def authenticate(self, token, purpose="login"):
        with self.db.connect() as db:
            row = db.execute(
                "SELECT * FROM sessions WHERE token_hash=? AND purpose=? AND expires_at>?",
                (digest(token), purpose, time.time()),
            ).fetchone()
            require(row is not None, "会话已失效，请重新验证身份", 401)
            if purpose == "login":
                return active_user(db, row["user_id"])
            return row["user_id"]

    def logout(self, token):
        with self.db.transaction(None, "LOGOUT") as db:
            db.execute("DELETE FROM sessions WHERE token_hash=?", (digest(token),))

    def reset_password(self, email, code, password):
        email = self.normalize_email(email)
        encoded = password_hash(password)
        self.verify_code(email, "reset", code)
        with self.db.transaction(None, "RESET_PASSWORD", "user") as db:
            row = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
            require(row, "无法重置该账户", 400)
            db.execute("UPDATE users SET password_hash=? WHERE id=?", (encoded, row[0]))
            db.execute("DELETE FROM sessions WHERE user_id=?", (row[0],))

    def appeal_token(self, email, code):
        email = self.normalize_email(email)
        self.verify_code(email, "appeal", code)
        with self.db.transaction(None, "APPEAL_IDENTITY") as db:
            row = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
            require(row, "无法验证该账户", 400)
            token = secrets.token_urlsafe(32)
            db.execute(
                "INSERT INTO sessions VALUES(?,?,'appeal',?)",
                (digest(token), row[0], time.time() + 1800),
            )
            return token
