"""HTTP 适配层：表单、CSRF、身份解析与业务服务调用。"""

import os
import secrets
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import (
    Flask,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_wtf.csrf import CSRFError, CSRFProtect, generate_csrf
from werkzeug.exceptions import HTTPException

from . import services_at
from .domain import STATUS_LABELS, BusinessError, require
from .moderation import AnalyticsLogService, ComplaintService
from .products import ProductService
from .trading import ReservationService, TransactionService


def integer(value, label="标识", default=None):
    if value in (None, "") and default is not None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError) as exc:
        raise BusinessError(f"{label}必须是整数", 400) from exc


def create_app(instance=None, config=None):
    instance = Path(instance or os.environ.get("MARKET_INSTANCE", "instance")).resolve()
    instance.mkdir(parents=True, exist_ok=True)
    secret_path = instance / "session-secret"
    if not secret_path.exists():
        with secret_path.open("x") as stream:
            stream.write(secrets.token_hex(32))
        secret_path.chmod(0o600)
    app = Flask(__name__, instance_path=str(instance))
    app.config.update(
        SECRET_KEY=secret_path.read_text().strip(),
        MAX_CONTENT_LENGTH=6 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("MARKET_HTTPS") == "1",
    )
    app.config.update(config or {})
    CSRFProtect(app)
    database, accounts = services_at(instance)
    products = ProductService(database, instance / "images")
    reservations, trades = ReservationService(database), TransactionService(database)
    complaints, analytics = ComplaintService(database), AnalyticsLogService(database)
    app.extensions["market"] = dict(
        database=database,
        accounts=accounts,
        products=products,
        reservations=reservations,
        trades=trades,
        complaints=complaints,
        analytics=analytics,
    )

    @app.before_request
    def identify():
        g.user = None
        if session.get("token"):
            try:
                g.user = accounts.authenticate(session["token"])
            except BusinessError:
                session.pop("token", None)

    @app.after_request
    def headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; "
            "base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        )
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.context_processor
    def context():
        return dict(
            user=getattr(g, "user", None),
            labels=STATUS_LABELS,
            request_key=lambda: secrets.token_hex(16),
            categories=database.rows("SELECT * FROM categories ORDER BY id"),
            email_demo=accounts.email_service.smtp is None,
        )

    @app.template_filter("money")
    def money(value):
        return f"{value / 100:,.2f}"

    @app.template_filter("localtime")
    def localtime(value):
        return (
            datetime.fromtimestamp(value, ZoneInfo("Asia/Shanghai")).strftime("%m-%d %H:%M")
            if value
            else "—"
        )

    def actor(admin=False):
        require(g.user, "请先登录", 401)
        require(not admin or g.user.is_admin, "需要管理员权限", 403)
        return g.user.user_id

    def verified_appeal_user():
        if g.user:
            return g.user.user_id
        require(session.get("appeal_token"), "请先完成申诉邮箱核验", 401)
        return accounts.authenticate(session["appeal_token"], "appeal")

    def done(target="index", **kwargs):
        if request.path.startswith("/api/"):
            return jsonify(ok=True, **kwargs)
        return redirect(url_for(target, **kwargs))

    @app.errorhandler(BusinessError)
    def business_error(error):
        if request.path.startswith("/api/"):
            return jsonify(error=str(error)), error.status
        return render_template("error.html", message=str(error)), error.status

    @app.errorhandler(CSRFError)
    def csrf_error(_error):
        return business_error(BusinessError("表单已过期或缺少安全令牌，请刷新页面", 400))

    @app.errorhandler(HTTPException)
    def http_error(error):
        return business_error(
            BusinessError(
                {404: "页面不存在", 413: "上传文件过大"}.get(error.code, "请求无法处理"), error.code
            )
        )

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            items=products.search(request.args),
            filters=request.args,
            heading="发现校园好物",
            mine=False,
            admin=False,
        )

    @app.get("/mine")
    def mine():
        return render_template(
            "index.html",
            items=products.search(request.args, actor(), mine=True),
            filters=request.args,
            heading="我的商品",
            mine=True,
            admin=False,
        )

    @app.get("/products/<int:product_id>")
    def detail(product_id):
        return render_template(
            "detail.html", item=products.detail(product_id, g.user.user_id if g.user else None)
        )

    @app.route("/edit", methods=["GET", "POST"])
    @app.route("/edit/<int:product_id>", methods=["GET", "POST"])
    def edit(product_id=None):
        owner = actor()
        item = products.detail(product_id, owner) if product_id else None
        require(not item or item["seller_id"] == owner, "只能编辑自己的商品", 403)
        if request.method == "GET":
            return render_template("edit.html", item=item)
        keys = request.form.getlist("image_keys")
        for image in request.files.getlist("images"):
            if image.filename:
                keys.append(products.upload(owner, image.read()))
        data = request.form.to_dict() | {"image_keys": keys}
        pid = products.save(
            owner,
            data,
            request.form.get("request_key"),
            product_id,
            integer(request.form.get("revision"), default=0),
            request.form.get("submit") == "review",
        )
        return redirect(url_for("detail", product_id=pid))

    @app.get("/images/<key>")
    def image(key):
        path = products.image_path(key, g.user.user_id if g.user else None)
        return send_file(path, mimetype="image/jpeg")

    @app.route("/auth/<mode>", methods=["GET", "POST"])
    @app.post("/api/login")
    def auth(mode="login"):
        require(
            mode in {"login", "register", "reset", "appeal", "code", "logout"}, "页面不存在", 404
        )
        if request.method == "GET":
            require(mode not in {"code", "logout"}, "请使用表单提交", 405)
            return render_template("auth.html", mode=mode)
        data = request.get_json() if request.is_json else request.form
        require(isinstance(data, Mapping), "请求内容必须是表单或 JSON 对象", 400)
        if mode == "login":
            token = accounts.login(data.get("email"), data.get("password", ""))
            if session.get("token"):
                accounts.logout(session["token"])
            session.clear()
            session["token"] = token
            if request.is_json:
                return jsonify(ok=True, csrf_token=generate_csrf())
            return done()
        if mode == "logout":
            if session.get("token"):
                accounts.logout(session["token"])
            if session.get("appeal_token"):
                accounts.logout(session["appeal_token"])
            session.clear()
            return done()
        if mode == "code":
            purpose = data.get("purpose")
            accounts.send_code(data.get("email"), purpose)
            return render_template(
                "notice.html",
                message="验证码已发送，请完成验证。开发模式请查看本机 outbox。",
                target=url_for("auth", mode=purpose),
            )
        if mode == "register":
            accounts.register(
                data.get("email"), data.get("nickname"), data.get("password"), data.get("code")
            )
            return done("auth", mode="login")
        if mode == "reset":
            accounts.reset_password(data.get("email"), data.get("code"), data.get("password"))
            return done("auth", mode="login")
        session["appeal_token"] = accounts.appeal_token(data.get("email"), data.get("code"))
        return done("appeals")

    @app.get("/bookings")
    def bookings():
        rows, waiting = reservations.dashboard(actor())
        return render_template("bookings.html", bookings=rows, waiting=waiting)

    @app.get("/bookings/<int:booking_id>/messages")
    def messages(booking_id):
        rows = reservations.messages(actor(), booking_id)
        return render_template("messages.html", messages=rows, booking_id=booking_id)

    @app.get("/appeals")
    def appeals():
        actions, rows, reports = complaints.personal(verified_appeal_user())
        return render_template("appeals.html", actions=actions, appeals=rows, complaints=reports)

    @app.get("/admin")
    def admin():
        uid = actor(admin=True)
        users, reports, appeals = complaints.admin_data(uid)
        return render_template(
            "admin.html",
            items=products.search(actor=uid, admin=True),
            users=users,
            complaints=reports,
            appeals=appeals,
            stats=analytics.statistics(uid),
        )

    @app.get("/admin/logs")
    def logs():
        filters = request.args.to_dict()
        for field in ("start", "end"):
            if filters.get(field):
                try:
                    filters[field] = (
                        datetime.fromisoformat(filters[field])
                        .replace(tzinfo=ZoneInfo("Asia/Shanghai"))
                        .timestamp()
                    )
                except ValueError as exc:
                    raise BusinessError("时间格式无效", 400) from exc
        return render_template("logs.html", rows=analytics.logs(actor(True), filters))

    @app.get("/api/session")
    def api_session():
        return jsonify(csrf_token=generate_csrf(), user_id=g.user.user_id if g.user else None)

    @app.get("/api/products")
    def api_products():
        return jsonify(items=products.search(request.args))

    @app.get("/api/products/<int:product_id>")
    def api_product(product_id):
        return jsonify(products.detail(product_id, g.user.user_id if g.user else None))

    @app.post("/api/actions/<action>")
    @app.post("/actions/<action>")
    def action(action):
        data = request.get_json() if request.is_json else request.form
        require(isinstance(data, Mapping), "请求内容必须是表单或 JSON 对象", 400)
        target_id = integer(data.get("id"))
        revision = integer(data.get("revision"), default=0)
        if action == "appeal":
            complaints.appeal(verified_appeal_user(), target_id, data.get("content"))
            return done("appeals")
        uid = actor()
        if action in {"reserve", "waitlist"}:
            method = reservations.reserve if action == "reserve" else reservations.join_waitlist
            result_id = method(uid, target_id, revision)
            return done("bookings", **({"result_id": result_id} if request.is_json else {}))
        if action == "offline":
            products.offline(uid, target_id, revision)
            return done("mine")
        if action == "complain":
            complaints.complain(uid, target_id, data.get("reason"))
            return done("appeals")
        if action in {"cancel", "accept", "price", "confirm", "withdraw", "promote", "message"}:
            if action == "cancel":
                reservations.cancel(uid, target_id)
            elif action == "accept":
                reservations.accept(uid, target_id)
            elif action == "price":
                reservations.accept_price(uid, target_id, revision)
            elif action == "confirm":
                trades.confirm(uid, target_id, revision)
            elif action == "withdraw":
                reservations.withdraw(uid, target_id)
            elif action == "promote":
                reservations.promote(uid, target_id, revision)
            else:
                reservations.message(uid, target_id, data.get("content"))
            return done("bookings")
        actor(admin=True)
        if action == "review":
            products.review(
                uid,
                target_id,
                integer(data.get("version_id")),
                revision,
                data.get("decision") == "approve",
                data.get("opinion"),
            )
        elif action == "moderate-product":
            require(data.get("verified") == "yes", "请先核实违规情况", 400)
            complaints.moderate_product(
                uid, target_id, revision, data.get("decision"), data.get("reason")
            )
        elif action == "moderate-user":
            complaints.moderate_user(
                uid,
                target_id,
                data.get("decision"),
                data.get("reason"),
                integer(data.get("hours"), "冻结时长", 24),
            )
        elif action == "resolve-complaint":
            complaints.resolve_complaint(
                uid, target_id, data.get("decision") == "approve", data.get("result")
            )
        elif action == "resolve-appeal":
            complaints.resolve_appeal(
                uid, target_id, data.get("decision") == "approve", data.get("result")
            )
        elif action == "create-admin":
            accounts.create_admin(
                uid, data.get("email"), data.get("nickname"), data.get("password")
            )
        else:
            raise BusinessError("操作不存在", 404)
        return done("admin")

    return app
