"""显式初始化命令；不在导入或启动时重置业务数据。"""

import argparse
import getpass
import os
from pathlib import Path

from . import services_at
from .domain import BusinessError


def main():
    parser = argparse.ArgumentParser(description="南京大学校园二手交易系统")
    parser.add_argument("command", choices=["init-db", "init-admin", "seed-demo", "run"])
    parser.add_argument("--instance", default="instance")
    parser.add_argument("--email", default="admin@nju.edu.cn")
    parser.add_argument("--port", type=int, default=5001)
    parser.add_argument("--count", type=int, default=8)
    parser.add_argument("--buyers", type=int, default=3)
    parser.add_argument("--https", action="store_true", help="使用临时自签名证书在本机演示 HTTPS")
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
    elif args.command == "seed-demo":
        from .demo import seed_demo

        try:
            seed_demo(
                database,
                accounts,
                Path(args.instance).resolve() / "images",
                args.count,
                args.buyers,
            )
        except BusinessError as exc:
            parser.exit(1, f"{exc}\n")
        print("虚构演示数据已创建；演示账号和口令见 README。")
    elif args.command == "run":
        from .web import create_app

        if not database.path.exists():
            parser.exit(1, "请先执行 init-db 和 init-admin。\n")
        app = create_app(args.instance, {"SESSION_COOKIE_SECURE": args.https})
        if args.https:
            app.run(host="127.0.0.1", port=args.port, ssl_context="adhoc", threaded=True)
        else:
            from waitress import serve

            serve(app, host="127.0.0.1", port=args.port, threads=24)


if __name__ == "__main__":
    main()
