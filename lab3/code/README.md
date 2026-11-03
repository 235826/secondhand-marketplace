# 校园二手交易系统 · 实验三

实现方案见上级目录的 `implementation-plan.md`。Python 3.13，SQLite，本地浏览器运行。

当前阶段：数据库、账户服务、商品图片及版本审核、查询、预约候补、重审改价、私有留言与双方成交服务及其测试。Web 界面和管理入口将在后续阶段加入。

```sh
cd lab3/code
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m marketplace init-db
.venv/bin/python -m marketplace init-admin --email admin@nju.edu.cn
.venv/bin/python -m pytest
.venv/bin/ruff check .
```

初始管理员通过显式初始化命令创建；开发邮件写入本机 instance/outbox，不能证明真实邮箱归属，也不提供公开读取接口。运行数据与本地密钥不提交 Git。
