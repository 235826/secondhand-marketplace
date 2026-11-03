"""南京大学校园二手交易系统。"""

from pathlib import Path

from .accounts import AccountService, EmailService
from .storage import Database


def services_at(instance):
    instance = Path(instance)
    database = Database(instance / "marketplace.sqlite3")
    return database, AccountService(database, EmailService(instance / "outbox"))
