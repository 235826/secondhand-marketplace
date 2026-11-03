# 南大二手 · 校园闲置交易

软件工程实验三，241220131 单锦曼。Python 3.13 + Flask + SQLite，支持桌面和移动浏览器。

## 安装与启动

在项目根目录执行，依赖已固定版本；首次安装需要网络。

若使用提交 ZIP，先进入解压目录下的 `code/`，从下面的 `python3 -m venv .venv` 开始执行，无需再运行 `cd lab3/code`。

```sh
cd lab3/code
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m marketplace init-db
.venv/bin/python -m marketplace init-admin --email admin@nju.edu.cn
.venv/bin/python -m marketplace seed-demo
.venv/bin/python -m marketplace run --port 5001
```

打开 http://127.0.0.1:5001 。`init-admin` 交互输入至少 10 字符的密码，也可使用 `MARKET_ADMIN_PASSWORD` 环境变量；不要将真实密码写入命令历史。初始化不会清空已有数据，重复创建初始管理员或演示数据会明确拒绝。普通启动不写入演示数据。

| 演示身份 | 邮箱 | 密码 |
|---|---|---|
| 初始管理员 | 初始化时指定，默认 admin@nju.edu.cn | 初始化时自行设置 |
| 卖家 | demo-seller@nju.edu.cn | Campus-demo-2026 |
| 买家 | demo-buyer1@nju.edu.cn，buyer2、buyer3 同理 | Campus-demo-2026 |

这些账户、数据、密码和图片均为本地实验专用。演示图片是程序绘制的示意图，不代表商品实物。管理员截图验收脚本使用 `Campus-admin-2026` 作为临时演示管理员口令；使用该脚本应创建独立测试 instance，勿复用个人账号。

## 功能与演示顺序

1. 卖家中心发布商品，填写八类信息及至少一张图片，保存草稿或送审。
2. 管理员工作台展开商品，检查内容与图片，审核通过或填写理由驳回。
3. 买家搜索商品并预约，成功即锁定；其他买家可主动选择候补。
4. 卖家确认或拒绝预约；候补不会自动转正，须按有效加入顺序明确确认。
5. 在线下面交后，买卖双方分别确认成交。单方确认不成交，成交后禁止撤销。
6. 已预约商品修改送审时，原锁定保留但暂停成交；新价通过后买家先接受新价格，再重新进行双方确认。
7. 预约留言仅双方可读；投诉由管理员核实，冻结/封禁用户可从未登录申诉入口核验身份并申诉。
8. 管理员查看分类商品/累计成交统计、筛选成功及拒绝操作日志。删除商品保留成交和审计历史。

所有权限和版本判断均在服务端执行；表单及 JSON 写请求均启用 CSRF。公开详情与卖家预约数据不返回买家邮箱/手机号。管理员不能修改商品正文，只有初始管理员可创建管理员。

## 配置与 HTTPS

全部命令可用 `--instance /绝对路径` 指定隔离的数据库、图片、邮件和会话密钥目录。默认 `instance/`，不提交 Git。临时 session-secret 自动生成且设为仅当前用户可读写。

```sh
.venv/bin/python -m marketplace run --https --port 5003
```

此命令在回环地址以临时自签名证书演示 HTTPS，并启用 Secure 会话 cookie。浏览器会提示证书未受信任，不能把这当作已部署可信证书。HTTP 入口用于纯本地调试。部署可通过反向代理提供可信 TLS，设置 `MARKET_HTTPS=1` 启用 Secure cookie，并用 `marketplace.web.create_app` 创建 WSGI 应用；当前没有对外部署。

支持学校邮箱域名通过 `MARKET_EMAIL_DOMAINS`（逗号分隔）配置，实验默认 `nju.edu.cn,smail.nju.edu.cn`。验证码用途隔离、10 分钟有效、单次使用、最多五次尝试，获取间隔不少于 60 秒。

默认邮件写入 `instance/outbox/*.json`，仅由演示者在本机查看，不向浏览器暴露读取入口；此模式不能证明真实邮箱归属。真实邮件配置使用环境变量 `MARKET_SMTP_HOST`、`MARKET_SMTP_PORT`（默认 465）、`MARKET_SMTP_USER`、`MARKET_SMTP_PASSWORD`、`MARKET_SMTP_SENDER`，通过 SMTP over TLS 发送。未配置和未实测真实 SMTP 时，不宣称真实发信验收通过。

## 代码组织

| 文件 | 职责 |
|---|---|
| marketplace/domain.py | 角色、状态、金额及输入校验；不依赖 Web/数据库 |
| marketplace/storage.py、schema.sql | SQLite 仓储、连接、事务、约束和审计写入 |
| marketplace/accounts.py | 注册登录、口令保护、邮件核验、服务端会话 |
| marketplace/products.py | 图片验证、不可变商品版本、审核、查询与可见性 |
| marketplace/trading.py | 预约、候补、留言、新价接受和成交确认 |
| marketplace/moderation.py | 投诉申诉、账户/商品处置、统计日志 |
| marketplace/web.py、templates/、static/ | HTTP 适配、表单和响应式页面 |
| marketplace/demo.py、__main__.py | 显式初始化、虚构数据及本机服务启动 |
| tests/ | 领域、权限、事务及 HTTP 集成测试 |
| scripts/ | 浏览器检查、负载测试、有效源码行数统计 |

相较最初计划，使用文件模块承载分层职责，避免为小型实验引入空的多级目录。SQLite Database 是具体仓储，不声称已实现 MySQL 适配。原 UML 的商品等实体映射为不可变版本表及应用服务，Python 领域角色保留继承；最新 UML 及报告解释对应关系。

## 验证

```sh
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m pytest -q
.venv/bin/python scripts/source_stats.py
```

完整浏览器检查会预约并成交商品 1、2，应在新建的独立演示 instance 执行；需要安装 Chromium（`.venv/bin/python -m playwright install chromium`），或通过 `--chromium /路径` 使用已有的 Chromium。脚本分别使用 1366×768、375×812 视口验证并保存截图。

```sh
.venv/bin/python scripts/browser_check.py --base http://127.0.0.1:5001 --output ../evidence/browser
```

性能测试在独立 instance 中初始化管理员，再执行 `seed-demo --count 500 --buyers 20`。使用相同 `--instance` 启动 HTTPS 服务后：

```sh
.venv/bin/python scripts/load_test.py --base https://127.0.0.1:5003 --insecure-local-tls --output ../evidence/load-results.json
```

默认持续 300 秒、20 独立会话，登录/列表/详情/预约请求比例约 10%/40%/30%/20%，预热不计入。预约冲突 409 单列为合法业务拒绝；非预期 HTTP 错误、超时和异常计入失败。`--insecure-local-tls` 仅供此自签名本地测试，测量的是服务端 HTTP 响应而非浏览器渲染时间。不能将该结果外推为上千用户容量。服务只监听 127.0.0.1。

项目 `.venv/`、`instance/`、数据库、cookie、验证码、密钥及缓存不得打包或提交。提交包仅包含代码、已公开的虚构账号说明、依赖清单和验证脚本。

参考：[Flask 官方教程](https://flask.palletsprojects.com/en/stable/tutorial/)、[Flask-WTF CSRF 文档](https://flask-wtf.readthedocs.io/en/1.2.x/csrf/)、[SQLite 部分唯一索引](https://www.sqlite.org/partialindex.html)。
