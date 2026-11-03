import re

import pytest
from test_trading import book, current

from marketplace.domain import BusinessError
from marketplace.moderation import AnalyticsLogService, ComplaintService
from marketplace.web import create_app


def test_complaint_appeal_and_account_sessions(market):
    m = market
    service = ComplaintService(m["db"])
    rid = book(m)
    cid = service.complain(m["other"], m["pid"], "请核实商品描述")
    with pytest.raises(BusinessError):
        service.complain(m["other"], m["pid"], "重复投诉")
    assert current(m)["status"] == "RESERVED"
    service.resolve_complaint(m["admin"], cid, True, "核实违规，暂时封禁")
    assert current(m)["status"] == "VIOLATION_BANNED"
    assert (
        m["db"].one("SELECT status FROM reservations WHERE id=?", (rid,))["status"] == "TERMINATED"
    )
    action = m["db"].one("SELECT * FROM moderation_actions")
    aid = service.appeal(m["seller"], action["id"], "已经修正，申请恢复")
    with pytest.raises(BusinessError):
        service.appeal(m["other"], action["id"], "冒用身份")
    service.resolve_appeal(m["admin"], aid, True, "同意解除，请重新送审")
    assert current(m)["status"] == "OFFLINE"
    assert m["products"].search() == []
    token = m["accounts"].login("buyer@smail.nju.edu.cn", "User-pass-2026")
    service.moderate_user(m["admin"], m["buyer"], "freeze", "临时限制")
    with pytest.raises(BusinessError):
        m["accounts"].authenticate(token)
    service.moderate_user(m["admin"], m["buyer"], "restore", "解除限制")
    with pytest.raises(BusinessError):
        m["accounts"].authenticate(token)


def test_deleted_product_preserves_trade_statistics_and_audit(market):
    m = market
    rid = book(m)
    m["reservations"].accept(m["seller"], rid)
    m["trades"].confirm(m["buyer"], rid, current(m)["revision"])
    m["trades"].confirm(m["seller"], rid, current(m)["revision"])
    service = ComplaintService(m["db"])
    analytics = AnalyticsLogService(m["db"])
    service.moderate_product(
        m["admin"], m["pid"], current(m)["revision"], "delete", "核实后删除展示"
    )
    assert m["products"].search() == []
    stats = analytics.statistics(m["admin"])
    assert sum(s["transactions"] for s in stats) == 1
    assert sum(s["products"] for s in stats) == 0
    assert analytics.logs(m["admin"], {"target_id": m["pid"], "action": "MODERATE_PRODUCT"})
    with pytest.raises(BusinessError):
        analytics.logs(m["buyer"])


@pytest.fixture
def web(market):
    m = market
    app = create_app(m["db"].path.parent, {"TESTING": True})
    return app, app.test_client(), m


def login(client, email, password="User-pass-2026"):
    csrf = client.get("/api/session").json["csrf_token"]
    response = client.post(
        "/api/login", json={"email": email, "password": password}, headers={"X-CSRFToken": csrf}
    )
    assert response.status_code == 200
    return client.get("/api/session").json["csrf_token"]


def test_all_pages_render_and_csrf_is_required(web):
    _, client, m = web
    for path in (
        "/",
        "/auth/login",
        "/auth/register",
        "/auth/reset",
        "/auth/appeal",
        f"/products/{m['pid']}",
    ):
        response = client.get(path)
        assert response.status_code == 200, response.data.decode()
        assert "Content-Security-Policy" in response.headers
    denied = client.post("/actions/reserve", data={"id": m["pid"]})
    assert denied.status_code == 400
    login(client, "seller@smail.nju.edu.cn")
    for path in ("/mine", "/edit", f"/edit/{m['pid']}", "/bookings", "/appeals"):
        assert client.get(path).status_code == 200, path
    assert client.get("/admin").status_code == 403
    login(client, "admin@nju.edu.cn", "Admin-pass-2026")
    assert client.get("/admin").status_code == 200
    assert client.get("/admin/logs").status_code == 200
    assert client.get(f"/edit/{m['pid']}").status_code == 403


def test_api_booking_privacy_and_malformed_requests(web):
    _, client, m = web
    csrf = login(client, "buyer@smail.nju.edu.cn")
    pid, revision = m["pid"], current(m)["revision"]
    assert b'action="/actions/reserve"' in client.get(f"/products/{pid}").data
    response = client.post(
        "/api/actions/reserve",
        json={"id": pid, "revision": revision},
        headers={"X-CSRFToken": csrf},
    )
    assert response.status_code == 200
    assert response.json["result_id"]
    bookings = client.get("/bookings")
    assert bookings.status_code == 200
    assert b"seller@smail" not in bookings.data
    assert b"buyer@smail" not in bookings.data
    rid = response.json["result_id"]
    assert client.get(f"/bookings/{rid}/messages").status_code == 200
    for payload in ({"id": "bad"}, {"id": pid, "revision": "bad"}):
        assert (
            client.post(
                "/api/actions/reserve", json=payload, headers={"X-CSRFToken": csrf}
            ).status_code
            == 400
        )
    login(client, "other@smail.nju.edu.cn")
    assert client.get(f"/bookings/{rid}/messages").status_code == 403
    assert client.get("/api/products").status_code == 200


def test_web_edit_and_review_via_forms(web):
    _, client, m = web
    login(client, "seller@smail.nju.edu.cn")
    html = client.get(f"/edit/{m['pid']}").data.decode()
    csrf = re.search('name="csrf_token" value="([^"]+)"', html)[1]
    request_key = re.search('name="request_key" value="([^"]+)"', html)[1]
    data = m["data"] | {
        "csrf_token": csrf,
        "request_key": request_key,
        "revision": str(current(m)["revision"]),
        "submit": "review",
    }
    response = client.post(f"/edit/{m['pid']}", data=data)
    assert response.status_code == 302
    assert current(m)["status"] == "PENDING_REVIEW"
    assert client.get("/").status_code == 200
    assert (
        b"\xe4\xba\x8c\xe6\x89\x8b\xe8\x87\xaa\xe8\xa1\x8c\xe8\xbd\xa6" not in client.get("/").data
    )
    csrf = login(client, "admin@nju.edu.cn", "Admin-pass-2026")
    item = current(m)
    response = client.post(
        "/actions/review",
        data={
            "id": m["pid"],
            "revision": item["revision"],
            "version_id": item["current_version_id"],
            "decision": "approve",
            "csrf_token": csrf,
        },
    )
    assert response.status_code == 302
    assert current(m)["status"] == "PUBLISHED"
