import io
import json
import uuid

import pytest
from PIL import Image

from marketplace import services_at
from marketplace.products import ProductService
from marketplace.trading import ReservationService, TransactionService


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


@pytest.fixture
def market(system, tmp_path):
    db, accounts, admin = system
    seller = register(accounts, "seller")
    buyer = register(accounts, "buyer")
    other = register(accounts, "other")
    products = ProductService(db, tmp_path / "images")
    reservations = ReservationService(db)
    trades = TransactionService(db)
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), "green").save(buffer, "PNG")
    image = products.upload(seller, buffer.getvalue())
    data = dict(
        title="二手自行车",
        description="校园通勤 Bicycle",
        category_id=4,
        price="100.00",
        condition="九成新",
        location="仙林校区",
        note="当面验货",
        image_keys=[image],
    )
    pid = products.save(seller, data, uuid.uuid4().hex, submit=True)
    pending = products.detail(pid, admin)
    products.review(admin, pid, pending["current_version_id"], pending["revision"], True)
    return dict(
        db=db,
        accounts=accounts,
        admin=admin,
        seller=seller,
        buyer=buyer,
        other=other,
        products=products,
        reservations=reservations,
        trades=trades,
        pid=pid,
        data=data,
    )
