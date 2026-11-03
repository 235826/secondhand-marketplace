import json

import pytest

from marketplace import services_at


@pytest.fixture
def system(tmp_path):
    db, accounts = services_at(tmp_path)
    db.initialize()
    admin = accounts.bootstrap("admin@nju.edu.cn", "Admin-pass-2026")
    return db, accounts, admin


def code_for(accounts, email, purpose="register"):
    accounts.send_code(email, purpose)
    paths = sorted(accounts.email_service.outbox.glob("*.json"), key=lambda p: p.stat().st_mtime_ns)
    return json.loads(paths[-1].read_text())["code"]


def register(accounts, name):
    email = f"{name}@smail.nju.edu.cn"
    code = code_for(accounts, email)
    return accounts.register(email, name, "User-pass-2026", code)
