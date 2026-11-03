"""预约、候补和双方成交；数据库事务保证并发一致性。"""

import time

from .domain import require, text
from .products import change_product, get_product
from .storage import active_user


class ReservationService:
    def __init__(self, database):
        self.db = database

    def _available(self, db, actor, product_id):
        active_user(db, actor, ordinary=True)
        product = get_product(db, product_id)
        require(product["seller_id"] != actor, "不能预约自己的商品", 403)
        require(
            not product["deleted_at"] and product["status"] in {"PUBLISHED", "RESERVED"},
            "当前商品不可预约或候补",
        )
        active_user(db, product["seller_id"])
        return product

    def reserve(self, actor, product_id, revision):
        with self.db.transaction(actor, "RESERVE", "product", product_id) as db:
            product = self._available(db, actor, product_id)
            require(product["revision"] == revision, "页面已过期，请刷新后再预约")
            require(product["status"] == "PUBLISHED", "商品已锁定，可主动选择加入候补")
            require(
                not db.execute(
                    "SELECT 1 FROM waitlists WHERE product_id=? AND buyer_id=? "
                    "AND status='WAITING'",
                    (product_id, actor),
                ).fetchone(),
                "请先退出候补再预约",
            )
            version = db.execute(
                "SELECT * FROM product_versions WHERE id=?", (product["approved_version_id"],)
            ).fetchone()
            booking = db.execute(
                "INSERT INTO reservations(product_id,buyer_id,status,accepted_price,"
                "accepted_version_id,created_at) VALUES(?,?,'LOCKED',?,?,?)",
                (product_id, actor, version["price_cents"], version["id"], time.time()),
            ).lastrowid
            change_product(db, actor, product, "RESERVED")
            return booking

    def join_waitlist(self, actor, product_id, revision):
        with self.db.transaction(actor, "JOIN_WAITLIST", "product", product_id) as db:
            product = self._available(db, actor, product_id)
            require(
                product["revision"] == revision and product["status"] == "RESERVED",
                "商品状态已变化，请刷新",
            )
            require(
                not db.execute(
                    "SELECT 1 FROM reservations WHERE product_id=? AND buyer_id=? "
                    "AND status IN ('LOCKED','SELLER_CONFIRMED')",
                    (product_id, actor),
                ).fetchone(),
                "已有正式预约，不能加入候补",
            )
            return db.execute(
                "INSERT INTO waitlists(product_id,buyer_id,status,joined_at) "
                "VALUES(?,?,'WAITING',?)",
                (product_id, actor, time.time()),
            ).lastrowid

    def withdraw(self, actor, waitlist_id):
        with self.db.transaction(actor, "WITHDRAW_WAITLIST", "waitlist", waitlist_id) as db:
            active_user(db, actor, ordinary=True)
            row = db.execute("SELECT * FROM waitlists WHERE id=?", (waitlist_id,)).fetchone()
            require(row and row["buyer_id"] == actor, "候补不存在或无权操作", 403)
            require(row["status"] == "WAITING", "该候补已经结束")
            db.execute("UPDATE waitlists SET status='CANCELLED' WHERE id=?", (waitlist_id,))

    def promote(self, actor, waitlist_id, revision):
        with self.db.transaction(actor, "PROMOTE_WAITLIST", "waitlist", waitlist_id) as db:
            active_user(db, actor, ordinary=True)
            waiting = db.execute("SELECT * FROM waitlists WHERE id=?", (waitlist_id,)).fetchone()
            require(waiting, "候补不存在", 404)
            product = get_product(db, waiting["product_id"])
            require(product["seller_id"] == actor, "只有卖家可以转正候补", 403)
            require(
                product["revision"] == revision
                and not product["deleted_at"]
                and product["status"] == "PUBLISHED",
                "商品已锁定或不可交易，请刷新",
            )
            require(waiting["status"] == "WAITING", "该候补已经结束")
            # 过期冻结账户先恢复；仍受限的队首被明确跳过并终止。
            rows = db.execute(
                "SELECT w.*,u.status AS user_status,u.frozen_until FROM waitlists w "
                "JOIN users u ON u.id=w.buyer_id WHERE w.product_id=? "
                "AND w.status='WAITING' ORDER BY w.joined_at,w.id",
                (product["id"],),
            ).fetchall()
            first = None
            for row in rows:
                eligible = row["user_status"] == "ACTIVE" or (
                    row["user_status"] == "FROZEN"
                    and row["frozen_until"] is not None
                    and row["frozen_until"] <= time.time()
                )
                if eligible:
                    first = row
                    break
            require(first and first["id"] == waitlist_id, "请先确认最早加入的有效候补")
            active_user(db, waiting["buyer_id"], ordinary=True)
            for row in rows:
                if row["id"] == waitlist_id:
                    break
                db.execute("UPDATE waitlists SET status='TERMINATED' WHERE id=?", (row["id"],))
            version = db.execute(
                "SELECT * FROM product_versions WHERE id=?", (product["approved_version_id"],)
            ).fetchone()
            now = time.time()
            booking = db.execute(
                "INSERT INTO reservations(product_id,buyer_id,status,accepted_price,"
                "accepted_version_id,seller_accepted_at,created_at) "
                "VALUES(?,?,'SELLER_CONFIRMED',?,?,?,?)",
                (
                    product["id"],
                    waiting["buyer_id"],
                    version["price_cents"],
                    version["id"],
                    now,
                    now,
                ),
            ).lastrowid
            db.execute("UPDATE waitlists SET status='PROMOTED' WHERE id=?", (waitlist_id,))
            change_product(db, actor, product, "RESERVED")
            return booking

    def _booking(self, db, actor, booking_id):
        active_user(db, actor, ordinary=True)
        booking = db.execute("SELECT * FROM reservations WHERE id=?", (booking_id,)).fetchone()
        require(booking, "预约不存在", 404)
        product = get_product(db, booking["product_id"])
        require(actor in {booking["buyer_id"], product["seller_id"]}, "无权操作他人预约", 403)
        return booking, product

    def accept(self, actor, booking_id):
        with self.db.transaction(actor, "ACCEPT_RESERVATION", "reservation", booking_id) as db:
            booking, product = self._booking(db, actor, booking_id)
            require(product["seller_id"] == actor, "仅卖家可确认预约", 403)
            require(booking["status"] in {"LOCKED", "SELLER_CONFIRMED"}, "预约已结束")
            require(product["status"] == "RESERVED" and not product["deleted_at"], "商品暂不可交易")
            active_user(db, booking["buyer_id"])
            db.execute(
                "UPDATE reservations SET status='SELLER_CONFIRMED',"
                "seller_accepted_at=coalesce(seller_accepted_at,?) WHERE id=?",
                (time.time(), booking_id),
            )

    def cancel(self, actor, booking_id):
        with self.db.transaction(actor, "CANCEL_RESERVATION", "reservation", booking_id) as db:
            booking, product = self._booking(db, actor, booking_id)
            require(booking["status"] in {"LOCKED", "SELLER_CONFIRMED"}, "预约已结束，不可取消")
            db.execute(
                "UPDATE reservations SET status='CANCELLED',buyer_trade_confirmed_at=NULL,"
                "seller_trade_confirmed_at=NULL,confirmation_version_id=NULL WHERE id=?",
                (booking_id,),
            )
            status = "PUBLISHED" if product["status"] == "RESERVED" else product["status"]
            change_product(db, actor, product, status)

    def accept_price(self, actor, booking_id, revision):
        with self.db.transaction(actor, "ACCEPT_PRICE", "reservation", booking_id) as db:
            booking, product = self._booking(db, actor, booking_id)
            require(booking["buyer_id"] == actor, "仅买家可以接受价格", 403)
            require(
                product["revision"] == revision
                and product["status"] == "RESERVED"
                and booking["status"] in {"LOCKED", "SELLER_CONFIRMED"},
                "版本或预约状态已变化",
            )
            version = db.execute(
                "SELECT * FROM product_versions WHERE id=?", (product["approved_version_id"],)
            ).fetchone()
            db.execute(
                "UPDATE reservations SET accepted_price=?,accepted_version_id=? WHERE id=?",
                (version["price_cents"], version["id"], booking_id),
            )

    def message(self, actor, booking_id, content):
        with self.db.transaction(actor, "RESERVATION_MESSAGE", "reservation", booking_id) as db:
            booking, product = self._booking(db, actor, booking_id)
            require(
                booking["status"] in {"LOCKED", "SELLER_CONFIRMED"} and not product["deleted_at"],
                "预约结束后只可查看历史留言",
            )
            db.execute(
                "INSERT INTO reservation_messages(reservation_id,sender_id,content,created_at) "
                "VALUES(?,?,?,?)",
                (booking_id, actor, text(content, "留言", 1000), time.time()),
            )

    def messages(self, actor, booking_id):
        with self.db.connect() as db:
            self._booking(db, actor, booking_id)
            return [
                dict(row)
                for row in db.execute(
                    "SELECT m.id,m.sender_id,u.nickname,m.content,m.created_at "
                    "FROM reservation_messages m "
                    "JOIN users u ON u.id=m.sender_id WHERE reservation_id=? ORDER BY m.id",
                    (booking_id,),
                )
            ]

    def dashboard(self, actor):
        with self.db.connect() as db:
            active_user(db, actor, ordinary=True)
            reservations = [
                dict(row)
                for row in db.execute(
                    "SELECT r.*,p.seller_id,p.revision,p.status AS product_status,v.title,"
                    "v.price_cents,v.id AS version_id,u.nickname AS buyer_name,"
                    "s.nickname AS seller_name "
                    "FROM reservations r JOIN products p ON p.id=r.product_id "
                    "JOIN product_versions v ON v.id=p.current_version_id "
                    "JOIN users u ON u.id=r.buyer_id JOIN users s ON s.id=p.seller_id "
                    "WHERE r.buyer_id=? OR p.seller_id=? ORDER BY r.id DESC",
                    (actor, actor),
                )
            ]
            waiting = [
                dict(row)
                for row in db.execute(
                    "SELECT w.*,p.seller_id,p.revision,p.status AS product_status,"
                    "v.title,u.nickname "
                    "FROM waitlists w JOIN products p ON p.id=w.product_id "
                    "JOIN product_versions v ON v.id=p.current_version_id "
                    "JOIN users u ON u.id=w.buyer_id "
                    "WHERE w.buyer_id=? OR p.seller_id=? ORDER BY w.joined_at,w.id",
                    (actor, actor),
                )
            ]
            return reservations, waiting


class TransactionService(ReservationService):
    def confirm(self, actor, booking_id, revision):
        with self.db.transaction(actor, "CONFIRM_TRANSACTION", "reservation", booking_id) as db:
            booking, product = self._booking(db, actor, booking_id)
            if booking["status"] == "COMPLETED":
                return db.execute(
                    "SELECT id FROM transactions WHERE reservation_id=?", (booking_id,)
                ).fetchone()[0]
            require(booking["status"] == "SELLER_CONFIRMED", "须先由卖家确认有效预约")
            require(
                product["status"] == "RESERVED"
                and not product["deleted_at"]
                and product["revision"] == revision,
                "商品正在重审或状态已变化，请刷新",
            )
            active_user(db, booking["buyer_id"])
            active_user(db, product["seller_id"])
            version = db.execute(
                "SELECT * FROM product_versions WHERE id=?", (product["approved_version_id"],)
            ).fetchone()
            require(
                booking["accepted_version_id"] == version["id"]
                and booking["accepted_price"] == version["price_cents"],
                "买家须先接受当前价格",
            )
            field = (
                "buyer_trade_confirmed_at"
                if actor == booking["buyer_id"]
                else "seller_trade_confirmed_at"
            )
            db.execute(
                f"UPDATE reservations SET {field}=coalesce({field},?),"
                "confirmation_version_id=? WHERE id=?",
                (time.time(), version["id"], booking_id),
            )
            updated = db.execute("SELECT * FROM reservations WHERE id=?", (booking_id,)).fetchone()
            if not (updated["buyer_trade_confirmed_at"] and updated["seller_trade_confirmed_at"]):
                return None
            transaction = db.execute(
                "INSERT INTO transactions(product_id,reservation_id,buyer_id,seller_id,version_id,"
                "price_cents,category_id,completed_at) VALUES(?,?,?,?,?,?,?,?)",
                (
                    product["id"],
                    booking_id,
                    booking["buyer_id"],
                    product["seller_id"],
                    version["id"],
                    version["price_cents"],
                    version["category_id"],
                    time.time(),
                ),
            ).lastrowid
            db.execute("UPDATE reservations SET status='COMPLETED' WHERE id=?", (booking_id,))
            db.execute(
                "UPDATE waitlists SET status='TERMINATED' WHERE product_id=? AND status='WAITING'",
                (product["id"],),
            )
            change_product(db, actor, product, "SOLD")
            return transaction
