import time

import pytest
from conftest import code_for, register

from marketplace.accounts import password_matches
from marketplace.domain import BusinessError


def test_registration_session_and_logout(system):
    db, accounts, _ = system
    user = register(accounts, "buyer")
    row = db.one("SELECT * FROM users WHERE id=?", (user,))
    assert row["password_hash"] != "User-pass-2026"
    assert password_matches("User-pass-2026", row["password_hash"])
    token = accounts.login("BUYER@SMAIL.NJU.EDU.CN", "User-pass-2026")
    assert accounts.authenticate(token).user_id == user
    accounts.logout(token)
    with pytest.raises(BusinessError):
        accounts.authenticate(token)
    assert "User-pass-2026" not in str(db.rows("SELECT * FROM operation_logs"))


def test_verification_retry_limit_and_one_time_use(system):
    db, accounts, _ = system
    email = "retry@nju.edu.cn"
    code = code_for(accounts, email)
    for _ in range(5):
        with pytest.raises(BusinessError):
            accounts.verify_code(email, "register", "invalid")
    with pytest.raises(BusinessError):
        accounts.verify_code(email, "register", code)
    assert db.one("SELECT attempts FROM email_challenges")["attempts"] == 6
    email = "once@nju.edu.cn"
    code = code_for(accounts, email)
    accounts.register(email, "昵称", "User-pass-2026", code)
    with pytest.raises(BusinessError):
        accounts.register(email, "昵称", "User-pass-2026", code)
    assert db.one("SELECT count(*) AS n FROM users WHERE email=?", (email,))["n"] == 1


def test_expired_codes_domains_and_password_validation(system):
    db, accounts, _ = system
    with pytest.raises(BusinessError):
        accounts.send_code("attacker@nju.edu.cn.evil.org", "register")
    code = code_for(accounts, "expired@nju.edu.cn")
    with db.connect() as connection:
        connection.execute("UPDATE email_challenges SET expires_at=0")
    with pytest.raises(BusinessError):
        accounts.register("expired@nju.edu.cn", "name", "User-pass-2026", code)
    with pytest.raises(BusinessError):
        accounts.bootstrap("other@nju.edu.cn", "weak")


def test_admin_creation_is_restricted(system):
    _, accounts, admin = system
    staff = accounts.create_admin(admin, "staff@nju.edu.cn", "管理员", "Staff-pass-2026")
    user = register(accounts, "ordinary")
    for actor in (staff, user):
        with pytest.raises(BusinessError):
            accounts.create_admin(actor, "forbidden@nju.edu.cn", "越权", "Staff-pass-2026")
    with pytest.raises(BusinessError):
        accounts.bootstrap("second@nju.edu.cn", "Admin-pass-2026")


def test_freeze_existing_session_and_expiry(system):
    db, accounts, _ = system
    user = register(accounts, "freeze")
    token = accounts.login("freeze@smail.nju.edu.cn", "User-pass-2026")
    with db.connect() as connection:
        connection.execute(
            "UPDATE users SET status='FROZEN',frozen_until=? WHERE id=?", (time.time() + 100, user)
        )
    with pytest.raises(BusinessError):
        accounts.authenticate(token)
    with db.connect() as connection:
        connection.execute("UPDATE users SET frozen_until=0 WHERE id=?", (user,))
    assert accounts.authenticate(token).user_id == user
    assert db.one("SELECT status FROM users WHERE id=?", (user,))["status"] == "ACTIVE"


def test_reset_revokes_sessions_and_appeal_token_is_restricted(system):
    db, accounts, _ = system
    user = register(accounts, "reset")
    token = accounts.login("reset@smail.nju.edu.cn", "User-pass-2026")
    with db.connect() as connection:
        connection.execute("UPDATE email_challenges SET created_at=0")
    code = code_for(accounts, "reset@smail.nju.edu.cn", "reset")
    accounts.reset_password("reset@smail.nju.edu.cn", code, "Changed-pass-2026")
    with pytest.raises(BusinessError):
        accounts.authenticate(token)
    with db.connect() as connection:
        connection.execute("UPDATE email_challenges SET created_at=0")
        connection.execute("UPDATE users SET status='BANNED' WHERE id=?", (user,))
    code = code_for(accounts, "reset@smail.nju.edu.cn", "appeal")
    limited = accounts.appeal_token("reset@smail.nju.edu.cn", code)
    assert accounts.authenticate(limited, "appeal") == user
    with pytest.raises(BusinessError):
        accounts.authenticate(limited)


def test_initialization_does_not_reset_existing_data(system):
    db, accounts, _ = system
    user = register(accounts, "persist")
    db.initialize()
    assert db.one("SELECT nickname FROM users WHERE id=?", (user,))["nickname"] == "persist"
