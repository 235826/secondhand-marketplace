"""投诉申诉、账户与商品处置、分类统计和审计查询。"""

import time

from .domain import require, text
from .products import change_product, get_product, terminate_bookings
from .storage import active_user, log


class ComplaintService:
    def __init__(self, database):
        self.db = database

    def complain(self, actor, product_id, reason):
        with self.db.transaction(actor, "COMPLAINT", "product", product_id) as db:
            active_user(db, actor, ordinary=True)
            product = get_product(db, product_id)
            require(
                not product["deleted_at"]
                and product["approved_version_id"]
                and product["status"] in {"PUBLISHED", "RESERVED", "OFFLINE", "SOLD"},
                "只能投诉公开商品",
            )
            require(product["seller_id"] != actor, "不能投诉自己的商品", 400)
            return db.execute(
                "INSERT INTO complaints(user_id,product_id,reason,created_at) VALUES(?,?,?,?)",
                (actor, product_id, text(reason, "投诉理由"), time.time()),
            ).lastrowid

    def resolve_complaint(self, actor, complaint_id, upheld, result):
        with self.db.transaction(actor, "RESOLVE_COMPLAINT", "complaint", complaint_id) as db:
            active_user(db, actor, admin=True)
            complaint = db.execute(
                "SELECT * FROM complaints WHERE id=?", (complaint_id,)
            ).fetchone()
            require(complaint and complaint["status"] == "PENDING", "投诉不存在或已处理")
            db.execute(
                "UPDATE complaints SET status=?,result=? WHERE id=?",
                ("RESOLVED" if upheld else "REJECTED", text(result, "处理意见"), complaint_id),
            )
            if upheld:
                self._product_action(db, actor, complaint["product_id"], "ban", result)

    def moderate_product(self, actor, product_id, revision, action, reason):
        with self.db.transaction(actor, "MODERATE_PRODUCT", "product", product_id) as db:
            active_user(db, actor, admin=True)
            product = get_product(db, product_id)
            require(product["revision"] == revision, "商品已变化，请刷新")
            self._product_action(db, actor, product_id, action, text(reason, "核实及处置理由"))

    def _product_action(self, db, actor, product_id, action, reason):
        require(action in {"offline", "ban", "delete"}, "处置操作无效", 400)
        product = get_product(db, product_id)
        require(not product["deleted_at"], "商品已删除")
        require(
            not (action == "offline" and product["status"] == "VIOLATION_BANNED"),
            "请先通过申诉解除违规限制",
        )
        terminate_bookings(db, product_id)
        db.execute("UPDATE products SET publication_blocked=1 WHERE id=?", (product_id,))
        if action == "delete" or product["status"] == "SOLD":
            db.execute(
                "UPDATE products SET deleted_at=?,revision=revision+1 WHERE id=?",
                (time.time(), product_id),
            )
        else:
            change_product(db, actor, product, "VIOLATION_BANNED" if action == "ban" else "OFFLINE")
        db.execute(
            "UPDATE moderation_actions SET active=0 WHERE target_type='product' "
            "AND target_id=? AND active=1",
            (product_id,),
        )
        db.execute(
            "INSERT INTO moderation_actions(admin_id,target_type,target_id,owner_id,"
            "action,reason,created_at) VALUES(?,'product',?,?,?,?,?)",
            (actor, product_id, product["seller_id"], action, reason, time.time()),
        )

    def moderate_user(self, actor, user_id, action, reason, hours=24):
        require(action in {"freeze", "ban", "restore"}, "账户操作无效", 400)
        require(isinstance(hours, int) and 1 <= hours <= 8760, "冻结时长须为 1～8760 小时", 400)
        with self.db.transaction(actor, "MODERATE_USER", "user", user_id) as db:
            active_user(db, actor, admin=True)
            user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
            require(user and user["role"] == "USER", "仅能处置普通账户", 403)
            reason = text(reason, "处置理由")
            status = {"freeze": "FROZEN", "ban": "BANNED", "restore": "ACTIVE"}[action]
            until = time.time() + hours * 3600 if action == "freeze" else None
            db.execute(
                "UPDATE users SET status=?,frozen_until=? WHERE id=?", (status, until, user_id)
            )
            db.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
            db.execute(
                "UPDATE moderation_actions SET active=0 WHERE target_type='user' "
                "AND target_id=? AND active=1",
                (user_id,),
            )
            db.execute(
                "INSERT INTO moderation_actions(admin_id,target_type,target_id,owner_id,"
                "action,reason,active,created_at) VALUES(?,'user',?,?,?,?,?,?)",
                (actor, user_id, user_id, action, reason, int(action != "restore"), time.time()),
            )
            log(db, actor, "ACCOUNT_STATE", "user", user_id, "SUCCESS", user["status"], status)

    def appeal(self, verified_user, moderation_id, content):
        # verified_user 由已登录会话或仅限申诉的核验会话提供，不能取自表单 user_id。
        with self.db.transaction(verified_user, "APPEAL", "moderation", moderation_id) as db:
            action = db.execute(
                "SELECT * FROM moderation_actions WHERE id=?", (moderation_id,)
            ).fetchone()
            require(
                action and action["owner_id"] == verified_user and action["active"],
                "无权申诉或该处置已解除",
                403,
            )
            return db.execute(
                "INSERT INTO appeals(user_id,moderation_id,content,created_at) VALUES(?,?,?,?)",
                (verified_user, moderation_id, text(content, "申诉理由"), time.time()),
            ).lastrowid

    def resolve_appeal(self, actor, appeal_id, approve, result):
        with self.db.transaction(actor, "RESOLVE_APPEAL", "appeal", appeal_id) as db:
            active_user(db, actor, admin=True)
            appeal = db.execute("SELECT * FROM appeals WHERE id=?", (appeal_id,)).fetchone()
            require(appeal and appeal["status"] == "SUBMITTED", "申诉不存在或已处理")
            action = db.execute(
                "SELECT * FROM moderation_actions WHERE id=?", (appeal["moderation_id"],)
            ).fetchone()
            result = text(result, "处理意见")
            if approve:
                require(action["active"], "原处置已被替代，请核对新处置")
                db.execute("UPDATE moderation_actions SET active=0 WHERE id=?", (action["id"],))
                if action["target_type"] == "user":
                    db.execute(
                        "UPDATE users SET status='ACTIVE',frozen_until=NULL WHERE id=?",
                        (action["target_id"],),
                    )
                    db.execute("DELETE FROM sessions WHERE user_id=?", (action["target_id"],))
                else:
                    product = get_product(db, action["target_id"])
                    # 撤销处罚仍不直接发布；已成交记录保持 SOLD。
                    db.execute("UPDATE products SET deleted_at=NULL WHERE id=?", (product["id"],))
                    if product["status"] != "SOLD":
                        change_product(db, actor, product, "OFFLINE")
            db.execute(
                "UPDATE appeals SET status=?,result=? WHERE id=?",
                ("APPROVED" if approve else "REJECTED", result, appeal_id),
            )

    def personal(self, verified_user):
        with self.db.connect() as db:
            actions = [
                dict(row)
                for row in db.execute(
                    "SELECT * FROM moderation_actions WHERE owner_id=? ORDER BY id DESC",
                    (verified_user,),
                )
            ]
            appeals = [
                dict(row)
                for row in db.execute(
                    "SELECT * FROM appeals WHERE user_id=? ORDER BY id DESC", (verified_user,)
                )
            ]
            complaints = [
                dict(row)
                for row in db.execute(
                    "SELECT * FROM complaints WHERE user_id=? ORDER BY id DESC", (verified_user,)
                )
            ]
            return actions, appeals, complaints

    def admin_data(self, actor):
        with self.db.connect() as db:
            active_user(db, actor, admin=True)
            users = [
                dict(row)
                for row in db.execute(
                    "SELECT id,nickname,email,role,status,frozen_until FROM users ORDER BY id"
                )
            ]
            complaints = [
                dict(row) for row in db.execute("SELECT * FROM complaints ORDER BY id DESC")
            ]
            appeals = [dict(row) for row in db.execute("SELECT * FROM appeals ORDER BY id DESC")]
            return users, complaints, appeals


class AnalyticsLogService:
    def __init__(self, database):
        self.db = database

    def statistics(self, actor):
        with self.db.connect() as db:
            active_user(db, actor, admin=True)
            return [
                dict(row)
                for row in db.execute(
                    "SELECT c.id,c.name, (SELECT count(*) FROM products p JOIN product_versions v "
                    "ON v.id=p.approved_version_id WHERE v.category_id=c.id "
                    "AND p.deleted_at IS NULL AND p.publication_blocked=0 "
                    "AND p.status IN ('PUBLISHED','RESERVED','OFFLINE','SOLD')) AS products,"
                    "(SELECT count(*) FROM transactions t WHERE t.category_id=c.id) "
                    "AS transactions "
                    "FROM categories c ORDER BY c.id"
                )
            ]

    def logs(self, actor, filters=None):
        filters = filters or {}
        with self.db.connect() as db:
            active_user(db, actor, admin=True)
            where, values = [], []
            for field in ("actor_id", "action", "target_type", "target_id", "result"):
                if filters.get(field):
                    where.append(f"{field}=?")
                    values.append(filters[field])
            for field, operator in (("start", ">="), ("end", "<=")):
                if filters.get(field):
                    require(isinstance(filters[field], (int, float)), "时间条件无效", 400)
                    where.append(f"created_at{operator}?")
                    values.append(filters[field])
            sql = "SELECT * FROM operation_logs WHERE " + " AND ".join(where or ["1=1"])
            return [dict(row) for row in db.execute(sql + " ORDER BY id DESC LIMIT 300", values)]
