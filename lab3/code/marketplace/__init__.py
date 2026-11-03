"""南京大学校园二手交易系统。"""

import os
from pathlib import Path

from .accounts import AccountService, EmailService
from .storage import Database


def services_at(instance):
    instance = Path(instance)
    database = Database(instance / "marketplace.sqlite3")
    smtp = None
    if os.environ.get("MARKET_SMTP_HOST"):
        smtp = {
            "host": os.environ["MARKET_SMTP_HOST"],
            "port": int(os.environ.get("MARKET_SMTP_PORT", "465")),
            "username": os.environ["MARKET_SMTP_USER"],
            "password": os.environ["MARKET_SMTP_PASSWORD"],
            "sender": os.environ["MARKET_SMTP_SENDER"],
        }
    domains = tuple(
        os.environ.get("MARKET_EMAIL_DOMAINS", "nju.edu.cn,smail.nju.edu.cn").split(",")
    )
    return database, AccountService(database, EmailService(instance / "outbox", smtp), domains)
