import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from conftest import register

from marketplace.domain import BusinessError
from marketplace.products import ProductService


def key():
    return uuid.uuid4().hex


def current(m):
    return m["products"].detail(m["pid"], m["seller"])


def book(m):
    return m["reservations"].reserve(m["buyer"], m["pid"], current(m)["revision"])


def test_review_validation_and_private_visibility(system, tmp_path):
    db, accounts, admin = system
    seller, other = register(accounts, "seller"), register(accounts, "other")
    products = ProductService(db, tmp_path)
    data = {"title": "草稿"}
    pid = products.save(seller, data, key())
    assert products.detail(pid, seller)["status"] == "DRAFT"
    assert products.search() == []
    with pytest.raises(BusinessError):
        products.detail(pid, other)
    with pytest.raises(BusinessError):
        products.save(seller, data, key(), pid, 2, submit=True)
    with pytest.raises(BusinessError):
        products.upload(seller, b"not an image")
    assert db.one("SELECT count(*) AS n FROM products")["n"] == 1


def test_owner_permissions_idempotency_and_search(market):
    m = market
    p = current(m)
    assert m["products"].search({"keyword": "BICYCLE", "min_price": "100", "max_price": "100"})
    assert not m["products"].search({"keyword": "%"})
    with pytest.raises(BusinessError):
        m["products"].search({"min_price": "200", "max_price": "100"})
    for actor in (m["other"], m["admin"]):
        with pytest.raises(BusinessError):
            m["products"].save(actor, m["data"], key(), m["pid"], p["revision"], submit=True)
    request = key()
    first = m["products"].save(m["seller"], {"title": "测试"}, request)
    assert first == m["products"].save(m["seller"], {"title": "测试"}, request)
    assert "email" not in str(m["products"].detail(m["pid"]))


def test_seller_acceptance_is_not_trade_and_completion_is_idempotent(market):
    m = market
    rid = book(m)
    m["reservations"].accept(m["seller"], rid)
    assert m["db"].rows("SELECT * FROM transactions") == []
    revision = current(m)["revision"]
    assert m["trades"].confirm(m["buyer"], rid, revision) is None
    tid = m["trades"].confirm(m["seller"], rid, revision)
    assert tid == m["trades"].confirm(m["seller"], rid, revision)
    assert current(m)["status"] == "SOLD"
    assert len(m["db"].rows("SELECT * FROM transactions")) == 1
    with pytest.raises(BusinessError):
        m["reservations"].cancel(m["buyer"], rid)
    with pytest.raises(BusinessError):
        m["products"].save(m["seller"], m["data"], key(), m["pid"], current(m)["revision"], True)


def test_reprice_requires_fresh_consent_and_confirmations(market):
    m = market
    rid = book(m)
    m["reservations"].accept(m["seller"], rid)
    m["trades"].confirm(m["seller"], rid, current(m)["revision"])
    p = current(m)
    data = m["data"] | {"price": "150.00"}
    m["products"].save(m["seller"], data, key(), m["pid"], p["revision"], True)
    assert m["products"].search() == []
    assert (
        m["db"].one("SELECT status FROM reservations WHERE id=?", (rid,))["status"]
        == "SELLER_CONFIRMED"
    )
    with pytest.raises(BusinessError):
        m["trades"].confirm(m["buyer"], rid, current(m)["revision"])
    p = current(m)
    m["products"].review(m["admin"], m["pid"], p["current_version_id"], p["revision"], True)
    assert current(m)["status"] == "RESERVED"
    revision = current(m)["revision"]
    with pytest.raises(BusinessError):
        m["trades"].confirm(m["buyer"], rid, revision)
    m["reservations"].accept_price(m["buyer"], rid, revision)
    assert m["trades"].confirm(m["buyer"], rid, revision) is None
    m["trades"].confirm(m["seller"], rid, revision)
    assert m["db"].one("SELECT price_cents FROM transactions")["price_cents"] == 15000


def test_cancel_during_rejected_review_keeps_hidden_and_stale_review_fails(market):
    m = market
    rid = book(m)
    p = current(m)
    m["products"].save(m["seller"], m["data"], key(), m["pid"], p["revision"], True)
    pending = current(m)
    m["products"].review(
        m["admin"], m["pid"], pending["current_version_id"], pending["revision"], False, "补充图片"
    )
    with pytest.raises(BusinessError):
        m["products"].review(
            m["admin"], m["pid"], pending["current_version_id"], pending["revision"], True
        )
    m["reservations"].cancel(m["buyer"], rid)
    assert current(m)["status"] == "REJECTED"
    assert m["products"].search() == []


def test_waitlist_order_explicit_promotion_and_offline(market):
    m = market
    rid = book(m)
    rev = current(m)["revision"]
    w1 = m["reservations"].join_waitlist(m["other"], m["pid"], rev)
    third = register(m["accounts"], "third")
    w2 = m["reservations"].join_waitlist(third, m["pid"], rev)
    with pytest.raises(BusinessError):
        m["reservations"].join_waitlist(m["other"], m["pid"], rev)
    m["reservations"].cancel(m["buyer"], rid)
    assert current(m)["status"] == "PUBLISHED"
    assert m["db"].one("SELECT status FROM waitlists WHERE id=?", (w1,))["status"] == "WAITING"
    with pytest.raises(BusinessError):
        m["reservations"].promote(m["seller"], w2, current(m)["revision"])
    m["reservations"].promote(m["seller"], w1, current(m)["revision"])
    assert current(m)["status"] == "RESERVED"
    m["products"].offline(m["seller"], m["pid"], current(m)["revision"])
    assert not m["db"].rows(
        "SELECT id FROM reservations WHERE status IN ('LOCKED','SELLER_CONFIRMED')"
    )
    assert not m["db"].rows("SELECT id FROM waitlists WHERE status='WAITING'")
    assert m["products"].search()[0]["status"] == "OFFLINE"


def test_message_privacy_and_cancel_invalidates_confirmation(market):
    m = market
    rid = book(m)
    m["reservations"].message(m["buyer"], rid, "明天食堂见")
    assert m["reservations"].messages(m["seller"], rid)[0]["content"] == "明天食堂见"
    for actor in (m["other"], m["admin"]):
        with pytest.raises(BusinessError):
            m["reservations"].messages(actor, rid)
    m["reservations"].accept(m["seller"], rid)
    m["trades"].confirm(m["buyer"], rid, current(m)["revision"])
    m["reservations"].cancel(m["seller"], rid)
    with pytest.raises(BusinessError):
        m["trades"].confirm(m["seller"], rid, current(m)["revision"])
    assert not m["db"].rows("SELECT id FROM transactions")


def test_20_buyers_concurrently_get_exactly_one_lock_each_round(market):
    m = market
    users = [register(m["accounts"], f"race{i}") for i in range(20)]
    for _ in range(3):
        revision = current(m)["revision"]
        barrier = Barrier(20)

        def attempt(user, barrier=barrier, revision=revision):
            barrier.wait()
            try:
                return user, m["reservations"].reserve(user, m["pid"], revision)
            except BusinessError:
                return None

        with ThreadPoolExecutor(max_workers=20) as pool:
            results = list(pool.map(attempt, users))
        successful = [result for result in results if result]
        assert len(successful) == 1
        assert len(m["db"].rows("SELECT * FROM reservations WHERE status='LOCKED'")) == 1
        m["reservations"].cancel(*successful[0])


def race_two(first, second):
    barrier = Barrier(2)

    def run(operation):
        barrier.wait()
        try:
            return operation()
        except BusinessError:
            return "DENIED"

    with ThreadPoolExecutor(max_workers=2) as pool:
        return list(pool.map(run, (first, second)))


def test_concurrent_cancel_and_final_confirmation_never_resurrects(market):
    m = market
    rid = book(m)
    m["reservations"].accept(m["seller"], rid)
    revision = current(m)["revision"]
    m["trades"].confirm(m["buyer"], rid, revision)
    race_two(
        lambda: m["trades"].confirm(m["seller"], rid, revision),
        lambda: m["reservations"].cancel(m["buyer"], rid),
    )
    status = m["db"].one("SELECT status FROM reservations WHERE id=?", (rid,))["status"]
    trades = m["db"].rows("SELECT * FROM transactions")
    assert (status == "COMPLETED" and len(trades) == 1 and current(m)["status"] == "SOLD") or (
        status == "CANCELLED" and not trades and current(m)["status"] == "PUBLISHED"
    )


def test_concurrent_promotion_and_new_buyer_have_one_lock(market):
    m = market
    rid = book(m)
    wid = m["reservations"].join_waitlist(m["other"], m["pid"], current(m)["revision"])
    m["reservations"].cancel(m["buyer"], rid)
    revision = current(m)["revision"]
    results = race_two(
        lambda: m["reservations"].promote(m["seller"], wid, revision),
        lambda: m["reservations"].reserve(m["buyer"], m["pid"], revision),
    )
    assert results.count("DENIED") == 1
    assert (
        len(
            m["db"].rows("SELECT * FROM reservations WHERE status IN ('LOCKED','SELLER_CONFIRMED')")
        )
        == 1
    )


def test_concurrent_review_only_first_decision_wins(market):
    m = market
    p = current(m)
    m["products"].save(m["seller"], m["data"], key(), m["pid"], p["revision"], True)
    pending = current(m)
    results = race_two(
        lambda: m["products"].review(
            m["admin"], m["pid"], pending["current_version_id"], pending["revision"], True
        ),
        lambda: m["products"].review(
            m["admin"],
            m["pid"],
            pending["current_version_id"],
            pending["revision"],
            False,
            "请补充信息",
        ),
    )
    assert results.count("DENIED") == 1
    assert (
        len(
            m["db"].rows(
                "SELECT * FROM review_records WHERE version_id=?", (pending["current_version_id"],)
            )
        )
        == 1
    )


def test_concurrent_reprice_and_final_confirmation_respects_version(market):
    m = market
    rid = book(m)
    m["reservations"].accept(m["seller"], rid)
    revision = current(m)["revision"]
    m["trades"].confirm(m["buyer"], rid, revision)
    results = race_two(
        lambda: m["trades"].confirm(m["seller"], rid, revision),
        lambda: m["products"].save(
            m["seller"], m["data"] | {"price": "150"}, key(), m["pid"], revision, True
        ),
    )
    assert results.count("DENIED") == 1
    if current(m)["status"] == "SOLD":
        assert m["db"].one("SELECT price_cents FROM transactions")["price_cents"] == 10000
    else:
        assert current(m)["status"] == "PENDING_REVIEW"
        assert not m["db"].rows("SELECT * FROM transactions")
        booking = m["db"].one("SELECT * FROM reservations WHERE id=?", (rid,))
        assert booking["buyer_trade_confirmed_at"] is None
