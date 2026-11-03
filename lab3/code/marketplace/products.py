"""商品版本、人工审核与按权限查询。"""

import io
import json
import secrets
import time
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from .domain import PUBLIC_STATUSES, BusinessError, cents, require, text
from .storage import active_user, log, receipt, remember


def get_product(db, product_id):
    row = db.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    require(row is not None, "商品不存在", 404)
    return row


def change_product(db, actor, product, status):
    db.execute(
        "UPDATE products SET status=?,revision=revision+1 WHERE id=?", (status, product["id"])
    )
    log(db, actor, "PRODUCT_STATE", "product", product["id"], "SUCCESS", product["status"], status)


def terminate_bookings(db, product_id):
    db.execute(
        "UPDATE reservations SET status='TERMINATED',buyer_trade_confirmed_at=NULL,"
        "seller_trade_confirmed_at=NULL,confirmation_version_id=NULL "
        "WHERE product_id=? AND status IN ('LOCKED','SELLER_CONFIRMED')",
        (product_id,),
    )
    db.execute(
        "UPDATE waitlists SET status='TERMINATED' WHERE product_id=? AND status='WAITING'",
        (product_id,),
    )


class ProductService:
    def __init__(self, database, image_dir):
        self.db = database
        self.image_dir = Path(image_dir)

    def upload(self, actor, content):
        require(0 < len(content) <= 5 * 1024 * 1024, "图片须小于 5 MB", 400)
        try:
            with Image.open(io.BytesIO(content)) as image:
                require(image.format in {"PNG", "JPEG", "WEBP"}, "仅支持 PNG/JPEG/WebP 图片", 400)
                require(image.width * image.height <= 20000000, "图片尺寸过大", 400)
                image.load()
                image = image.convert("RGB")
                image.thumbnail((1600, 1600))
                buffer = io.BytesIO()
                image.save(buffer, format="JPEG", quality=88)
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
            raise BusinessError("图片内容无效", 400) from exc
        key = secrets.token_hex(24) + ".jpg"
        with self.db.transaction(actor, "UPLOAD_IMAGE", "image") as db:
            active_user(db, actor, ordinary=True)
            self.image_dir.mkdir(parents=True, exist_ok=True)
            (self.image_dir / key).write_bytes(buffer.getvalue())
            db.execute("INSERT INTO media(key,owner_id) VALUES(?,?)", (key, actor))
        return key

    def save(self, actor, data, request_key, product_id=None, revision=None, submit=False):
        action = "SUBMIT_PRODUCT" if submit else "SAVE_DRAFT"
        with self.db.transaction(actor, action, "product", product_id) as db:
            active_user(db, actor, ordinary=True)
            previous = receipt(db, actor, action, request_key)
            if previous:
                return previous
            product = get_product(db, product_id) if product_id else None
            if product:
                require(product["seller_id"] == actor, "不能编辑他人商品", 403)
                require(
                    not product["deleted_at"]
                    and product["status"] not in {"SOLD", "VIOLATION_BANNED"},
                    "该商品不可编辑",
                )
                require(product["revision"] == revision, "商品已变化，请刷新")
                require(
                    not db.execute(
                        "SELECT 1 FROM moderation_actions WHERE target_type='product' "
                        "AND target_id=? AND active=1",
                        (product_id,),
                    ).fetchone(),
                    "请先通过申诉解除违规处置，再重新送审",
                )
                require(
                    submit or product["status"] in {"DRAFT", "REJECTED", "OFFLINE"},
                    "公开或待审商品修改后须重新送审",
                )
            title = text(data.get("title"), "名称", 100, submit)
            description = text(data.get("description"), "描述", 4000, submit)
            condition = text(data.get("condition"), "成色", 100, submit)
            location = text(data.get("location"), "交易地点", 200, submit)
            note = text(data.get("note"), "备注", 1000, submit)
            price = cents(data["price"]) if data.get("price") else 0
            require(not submit or price > 0, "请填写合法价格", 400)
            category_id = data.get("category_id") or None
            if category_id:
                require(
                    db.execute("SELECT 1 FROM categories WHERE id=?", (category_id,)).fetchone(),
                    "分类无效",
                    400,
                )
            require(not submit or category_id, "请选择分类", 400)
            keys = data.get("image_keys", [])
            require(isinstance(keys, list) and len(keys) <= 6, "最多上传六张图片", 400)
            require(not submit or keys, "送审需要至少一张图片", 400)
            for key in keys:
                require(isinstance(key, str), "图片标识无效", 400)
                require(
                    db.execute(
                        "SELECT 1 FROM media WHERE key=? AND owner_id=?", (key, actor)
                    ).fetchone(),
                    "图片不属于当前用户",
                    403,
                )
            now = time.time()
            if not product:
                product_id = db.execute(
                    "INSERT INTO products(seller_id,created_at) VALUES(?,?)", (actor, now)
                ).lastrowid
                product = get_product(db, product_id)
            version_no = db.execute(
                "SELECT coalesce(max(version_no),0)+1 FROM product_versions WHERE product_id=?",
                (product_id,),
            ).fetchone()[0]
            version_id = db.execute(
                "INSERT INTO product_versions(product_id,version_no,title,description,category_id,"
                "price_cents,condition,location,note,image_keys,created_at) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    product_id,
                    version_no,
                    title,
                    description,
                    category_id,
                    price,
                    condition,
                    location,
                    note,
                    json.dumps(keys),
                    now,
                ),
            ).lastrowid
            db.execute(
                "UPDATE products SET current_version_id=? WHERE id=?", (version_id, product_id)
            )
            status = "PENDING_REVIEW" if submit else product["status"]
            change_product(db, actor, product, status)
            if submit:
                db.execute(
                    "UPDATE reservations SET buyer_trade_confirmed_at=NULL,"
                    "seller_trade_confirmed_at=NULL,confirmation_version_id=NULL "
                    "WHERE product_id=? AND status IN ('LOCKED','SELLER_CONFIRMED')",
                    (product_id,),
                )
            remember(db, actor, action, request_key, product_id)
            return product_id

    def review(self, actor, product_id, version_id, revision, approve, opinion=""):
        with self.db.transaction(actor, "REVIEW_PRODUCT", "product", product_id) as db:
            active_user(db, actor, admin=True)
            product = get_product(db, product_id)
            require(
                not product["deleted_at"] and product["status"] == "PENDING_REVIEW",
                "商品不处于待审状态",
            )
            require(
                product["current_version_id"] == version_id and product["revision"] == revision,
                "审核版本已变化，请刷新",
            )
            opinion = text(opinion, "审核意见", 1000, not approve)
            db.execute(
                "INSERT INTO review_records(version_id,reviewer_id,conclusion,opinion,"
                "created_at) VALUES(?,?,?,?,?)",
                (version_id, actor, "APPROVED" if approve else "REJECTED", opinion, time.time()),
            )
            status = "REJECTED"
            if approve:
                locked = db.execute(
                    "SELECT 1 FROM reservations WHERE product_id=? AND "
                    "status IN ('LOCKED','SELLER_CONFIRMED')",
                    (product_id,),
                ).fetchone()
                status = "RESERVED" if locked else "PUBLISHED"
                db.execute(
                    "UPDATE products SET approved_version_id=?,"
                    "publication_blocked=0,published_at=coalesce(published_at,?) WHERE id=?",
                    (version_id, time.time(), product_id),
                )
                version = db.execute(
                    "SELECT price_cents FROM product_versions WHERE id=?", (version_id,)
                ).fetchone()
                db.execute(
                    "UPDATE reservations SET accepted_version_id=? WHERE product_id=? "
                    "AND accepted_price=? AND status IN ('LOCKED','SELLER_CONFIRMED')",
                    (version_id, product_id, version[0]),
                )
            change_product(db, actor, product, status)

    def offline(self, actor, product_id, revision):
        with self.db.transaction(actor, "OFFLINE_PRODUCT", "product", product_id) as db:
            active_user(db, actor, ordinary=True)
            product = get_product(db, product_id)
            require(product["seller_id"] == actor, "只能下架自己的商品", 403)
            require(not product["deleted_at"] and product["revision"] == revision, "商品已变化")
            require(
                product["status"] in {"PUBLISHED", "RESERVED", "PENDING_REVIEW", "REJECTED"},
                "当前状态不能下架",
            )
            terminate_bookings(db, product_id)
            change_product(db, actor, product, "OFFLINE")

    def detail(self, product_id, actor=None):
        with self.db.connect() as db:
            user = active_user(db, actor) if actor else None
            product = get_product(db, product_id)
            private = user and (user.is_admin or product["seller_id"] == actor)
            public = (
                product["status"] in PUBLIC_STATUSES
                and product["approved_version_id"]
                and not product["publication_blocked"]
            )
            require(private or (public and not product["deleted_at"]), "商品不可查看", 404)
            return self._view(db, product, private)

    def _view(self, db, product, private):
        version_id = product["current_version_id"] if private else product["approved_version_id"]
        version = dict(
            db.execute("SELECT * FROM product_versions WHERE id=?", (version_id,)).fetchone()
        )
        version.pop("id")
        version.pop("product_id")
        result = dict(product) | version
        result["image_keys"] = json.loads(result["image_keys"])
        result["seller_name"] = db.execute(
            "SELECT nickname FROM users WHERE id=?", (product["seller_id"],)
        ).fetchone()[0]
        result["category_name"] = "未分类"
        if version["category_id"]:
            result["category_name"] = db.execute(
                "SELECT name FROM categories WHERE id=?", (version["category_id"],)
            ).fetchone()[0]
        if private:
            result["reviews"] = [
                dict(row)
                for row in db.execute(
                    "SELECT r.*,v.version_no FROM review_records r JOIN product_versions v "
                    "ON v.id=r.version_id WHERE v.product_id=? ORDER BY r.id DESC",
                    (product["id"],),
                )
            ]
        return result

    def search(self, filters=None, actor=None, mine=False, admin=False):
        filters = filters or {}
        order = {
            "newest": "p.published_at DESC,p.id DESC",
            "oldest": "p.published_at,p.id",
            "price_asc": "v.price_cents,p.id",
            "price_desc": "v.price_cents DESC,p.id",
        }
        require(filters.get("sort", "newest") in order, "排序方式无效", 400)
        with self.db.connect() as db:
            user = active_user(db, actor, admin=admin) if actor else None
            require(not (mine or admin) or user, "请先登录", 401)
            private = mine or admin
            column = "current_version_id" if private else "approved_version_id"
            where, params = [], []
            if mine:
                where.append("p.seller_id=?")
                params.append(actor)
            if not admin:
                where.append("p.deleted_at IS NULL")
            if not private:
                where.append("p.status IN ('PUBLISHED','RESERVED','OFFLINE','SOLD')")
                where.append("p.publication_blocked=0")
            if filters.get("keyword"):
                # instr 避免用户输入的 % 和 _ 意外成为通配符。
                where.append(
                    "(instr(lower(v.title),lower(?))>0 OR instr(lower(v.description),lower(?))>0)"
                )
                params.extend([filters["keyword"], filters["keyword"]])
            for field, expression in (("category_id", "v.category_id=?"), ("status", "p.status=?")):
                if filters.get(field):
                    where.append(expression)
                    params.append(filters[field])
            lower = (
                cents(filters["min_price"], allow_zero=True)
                if filters.get("min_price") not in (None, "", "0")
                else 0
            )
            upper = (
                cents(filters["max_price"], allow_zero=True) if filters.get("max_price") else None
            )
            require(upper is None or lower <= upper, "价格下限不能大于上限", 400)
            where.append("v.price_cents>=?")
            params.append(lower)
            if upper is not None:
                where.append("v.price_cents<=?")
                params.append(upper)
            sql = (
                f"SELECT p.* FROM products p JOIN product_versions v ON v.id=p.{column} WHERE "
                + " AND ".join(where or ["1=1"])
                + " ORDER BY "
                + order[filters.get("sort", "newest")]
            )
            return [self._view(db, row, private) for row in db.execute(sql, params)]

    def image_path(self, key, actor=None):
        require(isinstance(key, str) and Path(key).name == key, "图片不存在", 404)
        with self.db.connect() as db:
            user = active_user(db, actor) if actor else None
            media = db.execute("SELECT owner_id FROM media WHERE key=?", (key,)).fetchone()
            require(media is not None, "图片不存在", 404)
            if user and (user.is_admin or media[0] == actor):
                return self.image_dir / key
            visible = db.execute(
                "SELECT v.image_keys FROM products p JOIN product_versions v "
                "ON v.id=p.approved_version_id WHERE p.deleted_at IS NULL "
                "AND p.publication_blocked=0 "
                "AND p.status IN ('PUBLISHED','RESERVED','OFFLINE','SOLD')"
            )
            require(any(key in json.loads(row[0]) for row in visible), "图片不可查看", 404)
            return self.image_dir / key
