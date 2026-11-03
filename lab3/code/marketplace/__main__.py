"""显式初始化命令；不在导入或启动时重置业务数据。"""

import argparse
import getpass
import os
from pathlib import Path

from . import services_at
from .domain import BusinessError


def main():
    parser = argparse.ArgumentParser(description="南京大学校园二手交易系统")
    parser.add_argument("command", choices=["init-db", "init-admin"])
    parser.add_argument("--instance", default="instance")
    parser.add_argument("--email", default="admin@nju.edu.cn")
    args = parser.parse_args()
    database, accounts = services_at(Path(args.instance).resolve())
    if args.command == "init-db":
        database.initialize()
        print("数据库已初始化；已有数据保留。")
    elif args.command == "init-admin":
        password = os.environ.get("MARKET_ADMIN_PASSWORD") or getpass.getpass("初始管理员密码：")
        try:
            accounts.bootstrap(args.email, password)
        except BusinessError as exc:
            parser.exit(1, f"{exc}\n")
        print("初始管理员已创建。")


if __name__ == "__main__":
    main()
