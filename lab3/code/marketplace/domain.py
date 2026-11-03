"""与框架无关的领域值、校验和权限语义。"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum


class BusinessError(Exception):
    """可向用户展示的业务拒绝，不包含底层数据库信息。"""

    def __init__(self, message, status=409):
        super().__init__(message)
        self.status = status


class ProductStatus(StrEnum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    REJECTED = "REJECTED"
    PUBLISHED = "PUBLISHED"
    RESERVED = "RESERVED"
    OFFLINE = "OFFLINE"
    SOLD = "SOLD"
    VIOLATION_BANNED = "VIOLATION_BANNED"


STATUS_LABELS = {
    "DRAFT": "草稿",
    "PENDING_REVIEW": "待审核",
    "REJECTED": "审核驳回",
    "PUBLISHED": "已发布",
    "RESERVED": "已预约",
    "OFFLINE": "已下架",
    "SOLD": "已成交",
    "VIOLATION_BANNED": "违规封禁",
    "LOCKED": "等待卖家确认",
    "SELLER_CONFIRMED": "卖家已确认预约",
    "CANCELLED": "已取消",
    "COMPLETED": "已成交",
    "TERMINATED": "已终止",
    "WAITING": "候补中",
    "PROMOTED": "已转正",
    "PENDING": "待处理",
    "RESOLVED": "已处理",
    "SUBMITTED": "待处理",
    "APPROVED": "已批准",
    "ACTIVE": "正常",
    "FROZEN": "冻结",
    "BANNED": "封禁",
    "USER": "普通用户",
    "ADMIN": "管理员",
    "INITIAL_ADMIN": "初始管理员",
}
ACTIVE_RESERVATIONS = ("LOCKED", "SELLER_CONFIRMED")
PUBLIC_STATUSES = ("PUBLISHED", "RESERVED", "OFFLINE", "SOLD")


@dataclass(frozen=True)
class User:
    user_id: int
    nickname: str
    role: str = "USER"

    @property
    def is_admin(self):
        return self.role in {"ADMIN", "INITIAL_ADMIN"}


@dataclass(frozen=True)
class Admin(User):
    role: str = "ADMIN"


@dataclass(frozen=True)
class InitialAdmin(Admin):
    role: str = "INITIAL_ADMIN"


def principal(row):
    cls = {"ADMIN": Admin, "INITIAL_ADMIN": InitialAdmin}.get(row["role"], User)
    return cls(row["id"], row["nickname"])


def require(condition, message, status=409):
    if not condition:
        raise BusinessError(message, status)


def text(value, label, maximum=2000, required=True):
    value = str(value or "").strip()
    require(not required or bool(value), f"请填写{label}", 400)
    require(len(value) <= maximum, f"{label}不能超过 {maximum} 字", 400)
    return value


def cents(value, allow_zero=False):
    try:
        number = Decimal(str(value))
        require(number.is_finite(), "价格必须为有限数值", 400)
        require(
            (number >= 0 if allow_zero else number > 0) and number <= Decimal("99999999.99"),
            "价格须在允许范围内",
            400,
        )
        require(number * 100 == (number * 100).to_integral_value(), "价格最多两位小数", 400)
        return int(number * 100)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise BusinessError("请输入合法价格", 400) from exc
