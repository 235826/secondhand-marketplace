from generate_ui import *


def screen_seller_products():
    b = [rect(0, 0, W, H, C["bg"]), header("seller")]
    b.append(page_title("卖家中心", "管理我的商品、预约与成交", 112,
                        button(1160, 96, 166, 42, "发布新商品", "primary", "plus")))
    stats = [("8", "在售商品", "正常展示中"), ("2", "待审核", "等待管理员处理"),
             ("3", "已预约", "等待确认或成交"), ("12", "已成交", "历史累计")]
    for i, (num, lab, sub) in enumerate(stats):
        x = 40 + i * 324
        b.append(rect(x, 158, 300, 88, "#FFFFFF", C["border"], rx=14, shadow=True))
        b.append(text(x + 20, 195, num, 26, C["text"], 700))
        b.append(text(x + 20, 220, lab, 13, C["text"], 600))
        b.append(text(x + 20, 236, sub, 11, C["muted"]))

    tabs = ["全部", "草稿", "待审核", "已发布", "已预约", "已下架", "已成交"]
    x = 40
    for i, name in enumerate(tabs):
        active = i == 0
        b.append(text(x, 292, name, 13, C["primary"] if active else C["muted"], 600 if active else 400))
        if active:
            b.append(rect(x, 306, len(name) * 13, 3, C["primary"], rx=2))
        x += len(name) * 13 + 36
    b.append(text(1090, 292, "共 25 件商品", 12, C["muted"]))

    b.append(rect(40, 322, 1286, 386, "#FFFFFF", C["border"], rx=14, shadow=True))
    b.append(rect(40, 322, 1286, 46, "#F9FAFB", rx=14))
    cols = [("商品", 70), ("分类", 470), ("价格", 586), ("状态", 680), ("预约", 800), ("更新时间", 900), ("操作", 1080)]
    for name, x in cols:
        b.append(text(x, 350, name, 12, C["muted"], 600))
    b.append(line(40, 368, 1326, 368, C["border"]))

    rows = [
        ("iPad Air 5 64G 蓝色", "数码产品", "¥ 2,680", "已预约", "1", "2026-10-28", "g1", "tablet"),
        ("高等数学教材 第七版", "图书", "¥ 25", "已发布", "0", "2026-10-27", "g2", "book"),
        ("捷安特山地自行车", "运动", "¥ 680", "已发布", "0", "2026-10-26", "g3", "bike"),
        ("索尼 WH-1000XM4 耳机", "数码产品", "¥ 1,150", "待审核", "0", "2026-10-25", "g5", "headphones"),
        ("护眼台灯 可调光", "生活用品", "¥ 45", "已下架", "0", "2026-10-24", "g4", "lamp"),
        ("斯伯丁篮球 7 号", "运动", "¥ 80", "已成交", "1", "2026-10-20", "g6", "ball"),
    ]
    for i, (title, cat, price, status, res, updated, grad, ic) in enumerate(rows):
        y = 368 + i * 52
        b.append(product_thumb(64, y + 8, 36, 36, grad, ic))
        b.append(text(112, y + 23, title, 13, C["text"], 600))
        b.append(text(112, y + 39, "ID: P-2026-10" + str(i + 1), 10, C["subtle"]))
        b.append(text(470, y + 30, cat, 12, C["muted"]))
        b.append(text(586, y + 30, price, 13, C["text"], 600))
        b.append(badge(680, y + 14, status))
        b.append(text(806, y + 30, res, 12, C["muted"]))
        b.append(text(900, y + 30, updated, 12, C["muted"]))
        b.append(text(1080, y + 30, "编辑", 12, C["primary"], 500))
        b.append(text(1130, y + 30, "查看", 12, C["primary"], 500))
        b.append(text(1180, y + 30, "下架" if status not in ("已成交", "已下架") else "删除", 12, C["muted"], 500))
        if i < len(rows) - 1:
            b.append(line(64, y + 52, 1302, y + 52, C["border"]))

    b.append(text(40, 742, "第 1 页 / 共 5 页", 12, C["muted"]))
    for i, page in enumerate(["1", "2", "3", "4", "5"]):
        x = 1180 + i * 30
        b.append(rect(x, 728, 26, 26, C["primary"] if page == "1" else "#FFFFFF", C["border"], rx=7))
        b.append(text(x + 13, 746, page, 11, "#FFFFFF" if page == "1" else C["muted"], 600, "middle"))
    return svg_doc(W, H, "".join(b))


def screen_edit_product():
    b = [rect(0, 0, W, H, C["bg"]), header("seller")]
    b.append(page_title("发布 / 编辑商品", "填写商品信息并提交管理员审核", 112))
    steps = [("1", "填写信息", True), ("2", "提交审核", False), ("3", "审核发布", False)]
    for i, (num, name, active) in enumerate(steps):
        x = 40 + i * 190
        b.append(circle(x + 14, 164, 14, C["primary"] if active else "#FFFFFF", C["primary"] if active else C["border"], 2))
        b.append(text(x + 14, 169, num, 13, "#FFFFFF" if active else C["muted"], 700, "middle"))
        b.append(text(x + 38, 169, name, 13, C["text"] if active else C["muted"], 600 if active else 400))
        if i < 2:
            b.append(line(x + 32, 164, x + 168, 164, C["border"]))

    b.append(rect(40, 200, 840, 520, "#FFFFFF", C["border"], rx=16, shadow=True))
    b.append(label(64, 236, "商品名称 *"))
    b.append(field(64, 244, 380, 44, "例如：iPad Air 5 64G 蓝色", value="iPad Air 5 64G 蓝色"))
    b.append(label(464, 236, "商品分类 *"))
    b.append(field(464, 244, 380, 44, "请选择分类", "chevron_down", "数码产品"))

    b.append(label(64, 310, "价格（元）*"))
    b.append(field(64, 318, 180, 44, "0.00", value="2680"))
    b.append(label(264, 310, "成色 *"))
    b.append(field(264, 318, 180, 44, "请选择成色", "chevron_down", "95 新"))
    b.append(label(464, 310, "交易地点 *"))
    b.append(field(464, 318, 380, 44, "例如：仙林校区 · 四组团", value="仙林校区 · 四组团"))

    b.append(label(64, 386, "商品图片 *"))
    for i in range(3):
        x = 64 + i * 132
        b.append(f'<rect x="{x}" y="396" width="118" height="80" rx="10" fill="#F9FAFB" stroke="{C["border"]}" stroke-width="1" stroke-dasharray="6 5"/>')
        b.append(icon("plus", x + 47, 420, 24, C["subtle"]))
        b.append(text(x + 59, 464, "上传图片", 10, C["subtle"], 400, "middle"))
    b.append(text(470, 420, "第一张图片将作为封面；支持 JPG / PNG，单张不超过 5MB。", 11, C["muted"]))
    b.append(text(470, 440, "至少上传 1 张，最多 9 张。", 11, C["muted"]))

    b.append(label(64, 506, "商品描述 *"))
    b.append(rect(64, 514, 780, 70, "#FFFFFF", C["border"], rx=10))
    b.append(multiline(78, 538, [
        "自用 iPad Air 5，64G，蓝色，无磕碰，电池健康 92%。含原装充电器和保护壳。",
        "因换新出售，可在仙林校区当面验机。",
    ], 12, C["muted"], 400, 20))

    b.append(label(64, 608, "备注 *"))
    b.append(rect(64, 616, 780, 58, "#FFFFFF", C["border"], rx=10))
    b.append(text(78, 638, "补充说明，例如发票、保修情况、可交易时间等。", 12, C["subtle"]))
    b.append(text(78, 658, "备注为必填项；提交审核前请确认信息完整、价格合法。", 11, C["warning"]))

    b.append(rect(910, 200, 416, 520, "#FFFFFF", C["border"], rx=16, shadow=True))
    b.append(text(934, 238, "发布须知", 17, C["text"], 700))
    rules = [
        "1. 商品需填写名称、描述、分类、价格、成色、图片、交易地点和备注。",
        "2. 提交后进入待审核状态，审核通过后才会公开。",
        "3. 修改已发布商品会进入重审，期间暂停成交。",
        "4. 不得发布违规物品；管理员有权下架或封禁。",
    ]
    b.append(multiline(934, 274, rules, 12, C["muted"], 400, 28))
    b.append(rect(934, 406, 368, 76, C["primary_light"], rx=10))
    b.append(icon("shield", 950, 424, 20, C["primary"]))
    b.append(text(980, 430, "审核通过后自动发布", 12, C["primary"], 700))
    b.append(text(980, 450, "审核一般在 1 个工作日内完成。", 11, C["muted"]))
    b.append(rect(934, 500, 368, 50, C["gray_light"], rx=10))
    b.append(text(950, 520, "当前状态", 11, C["muted"]))
    b.append(badge(1000, 508, "待审核"))
    b.append(text(1150, 520, "保存后仍可继续编辑", 11, C["muted"]))
    b.append(button(934, 620, 174, 46, "保存草稿", "secondary"))
    b.append(button(1124, 620, 178, 46, "提交审核", "primary", "check"))
    b.append(text(934, 692, "提交即表示你确认商品信息真实、合法。", 11, C["subtle"]))
    return svg_doc(W, H, "".join(b))


def screen_seller_reservations():
    b = [rect(0, 0, W, H, C["bg"]), header("seller")]
    b.append(page_title("预约与候补", "处理买家预约，维护商品交易状态", 112))
    b.append(rect(40, 150, 1286, 72, "#FFFFFF", C["border"], rx=14, shadow=True))
    b.append(product_thumb(56, 162, 48, 48, "g1", "tablet"))
    b.append(text(120, 180, "iPad Air 5 64G 蓝色", 15, C["text"], 600))
    b.append(text(120, 200, "¥ 2,680 · 仙林校区 · 卖家：单锦曼", 11, C["muted"]))
    b.append(badge(1040, 174, "已预约"))
    b.append(text(1140, 191, "切换商品  ›", 12, C["primary"], 500))

    b.append(rect(40, 242, 620, 330, "#FFFFFF", C["border"], rx=14, shadow=True))
    b.append(text(64, 278, "当前正式预约", 16, C["text"], 700))
    b.append(badge(520, 254, "待卖家确认"))
    b.append(avatar(64, 302, 44, "王", C["success"]))
    b.append(text(122, 320, "王同学", 14, C["text"], 600))
    b.append(text(122, 340, "预约时间 2026-10-29 10:12 · 信用 96", 11, C["muted"]))
    b.append(text(500, 320, "查看买家", 11, C["primary"], 500))
    steps = [("预约成功", True), ("卖家确认", False), ("双方成交", False)]
    for i, (name, done) in enumerate(steps):
        x = 72 + i * 180
        color = C["primary"] if done or i == 1 else C["border"]
        b.append(circle(x, 392, 12, C["primary"] if i <= 1 else "#FFFFFF", color, 2))
        if i <= 1:
            b.append(icon("check", x - 6, 386, 12, "#FFFFFF", 2))
        b.append(text(x, 424, name, 11, C["text"] if i <= 1 else C["muted"], 500, "middle"))
        if i < 2:
            b.append(line(x + 14, 392, x + 166, 392, C["border"]))
    b.append(rect(64, 454, 572, 56, C["gray_light"], rx=10))
    b.append(icon("alert", 80, 470, 18, C["warning"]))
    b.append(text(106, 478, "确认预约仅表示同意线下交易，不等于成交。", 11, C["muted"]))
    b.append(text(106, 496, "双方均确认成交后，交易才完成。", 11, C["muted"]))
    b.append(button(64, 526, 140, 40, "确认预约", "primary", "check"))
    b.append(button(216, 526, 120, 40, "拒绝预约", "danger"))
    b.append(button(348, 526, 120, 40, "取消预约", "secondary"))

    b.append(rect(680, 242, 646, 330, "#FFFFFF", C["border"], rx=14, shadow=True))
    b.append(text(704, 278, "候补队列", 16, C["text"], 700))
    b.append(text(780, 278, "（3 人）", 12, C["muted"]))
    b.append(text(1160, 278, "候补不占用锁定", 11, C["warning"]))
    waiters = [("1", "李同学", "10-29 11:05", "候补中", True), ("2", "张同学", "10-29 12:18", "候补中", False),
               ("3", "陈同学", "10-29 15:42", "候补中", False)]
    for i, (no, name, tm, st, can) in enumerate(waiters):
        y = 300 + i * 62
        b.append(circle(722, y + 16, 14, C["purple_light"]))
        b.append(text(722, y + 21, no, 12, C["purple"], 700, "middle"))
        b.append(text(750, y + 16, name, 13, C["text"], 600))
        b.append(text(750, y + 34, f"加入时间 {tm}", 10, C["muted"]))
        b.append(badge(1000, y + 4, st))
        b.append(button(1100, y + 2, 104, 32, "确认候补" if can else "查看", "primary" if can else "secondary", size=12))
        if i < 2:
            b.append(line(704, y + 56, 1302, y + 56, C["border"]))

    b.append(rect(40, 590, 1286, 142, "#FFFFFF", C["border"], rx=14, shadow=True))
    b.append(text(64, 622, "预约记录", 15, C["text"], 700))
    events = [("10-29 10:12", "王同学提交预约，取得唯一锁定", "系统"),
              ("10-29 10:15", "卖家查看预约详情", "单锦曼"),
              ("10-29 11:05", "李同学加入候补", "系统"),
              ("10-29 12:18", "张同学加入候补", "系统")]
    for i, (tm, action, who) in enumerate(events):
        y = 650 + i * 23
        b.append(text(64, y, tm, 11, C["muted"]))
        b.append(circle(156, y - 4, 3, C["primary"]))
        b.append(text(174, y, action, 11, C["text"]))
        b.append(text(1190, y, who, 11, C["muted"]))
    return svg_doc(W, H, "".join(b))


def screen_buyer_reservations():
    b = [rect(0, 0, W, H, C["bg"]), header("reservations")]
    b.append(page_title("我的预约", "查看预约进度并完成成交确认", 112))
    tabs = ["全部", "待卖家确认", "待成交", "已完成", "已取消"]
    x = 40
    for i, name in enumerate(tabs):
        active = i == 0
        b.append(text(x, 164, name, 13, C["primary"] if active else C["muted"], 600 if active else 400))
        if active:
            b.append(rect(x, 178, len(name) * 13, 3, C["primary"], rx=2))
        x += len(name) * 13 + 36

    cards = [
        ("iPad Air 5 64G 蓝色", "¥ 2,680", "卖家：李同学", "待成交", "g1", "tablet",
         "预约成功  →  卖家已确认  →  待你确认", "确认成交", "取消预约"),
        ("高等数学教材 第七版", "¥ 25", "卖家：张同学", "待卖家确认", "g2", "book",
         "预约成功  →  等待卖家确认", "取消预约", None),
        ("护眼台灯 可调光", "¥ 45", "卖家：陈同学", "已完成", "g4", "lamp",
         "预约成功  →  卖家已确认  →  成交完成", "查看商品", None),
    ]
    for i, (title, price, seller, status, grad, ic, timeline, action1, action2) in enumerate(cards):
        y = 200 + i * 166
        b.append(rect(40, y, 900, 150, "#FFFFFF", C["border"], rx=14, shadow=True))
        b.append(product_thumb(60, y + 24, 96, 96, grad, ic))
        b.append(text(176, y + 48, title, 15, C["text"], 700))
        b.append(text(176, y + 78, price, 20, C["primary"], 700))
        b.append(text(176, y + 100, seller, 11, C["muted"]))
        b.append(badge(790, y + 22, status))
        b.append(text(176, y + 124, timeline, 11, C["primary"], 500))
        b.append(button(700, y + 60, 132, 38, action1, "primary" if status == "待成交" else "secondary", size=12))
        if action2:
            b.append(button(700, y + 106, 132, 34, action2, "ghost", size=12))
        b.append(line(60, y + 150, 920, y + 150, C["border"], 0))

    b.append(rect(960, 200, 366, 482, "#FFFFFF", C["border"], rx=14, shadow=True))
    b.append(text(984, 236, "交易提示", 16, C["text"], 700))
    tips = [
        "预约成功即锁定商品，其他买家可加入候补。",
        "卖家确认预约后，双方自行线下交易。",
        "买卖双方均确认成交后，交易才完成。",
        "成交前可以取消；成交后不可撤销。",
    ]
    b.append(multiline(984, 272, tips, 12, C["muted"], 400, 26))
    b.append(rect(984, 402, 318, 82, C["primary_light"], rx=10))
    b.append(text(1000, 428, "我的成交", 12, C["primary"], 700))
    b.append(text(1000, 460, "12", 26, C["primary"], 700))
    b.append(text(1040, 460, "笔", 12, C["muted"]))
    b.append(text(1140, 428, "本月", 11, C["muted"]))
    b.append(button(984, 510, 318, 44, "查看全部订单", "secondary", "arrow_right"))
    b.append(rect(984, 578, 318, 80, C["gray_light"], rx=10))
    b.append(icon("shield", 1000, 596, 18, C["success"]))
    b.append(text(1028, 606, "交易安全提醒", 12, C["text"], 600))
    b.append(text(1028, 626, "请勿脱离平台私下转账。", 11, C["muted"]))
    return svg_doc(W, H, "".join(b))


def screen_admin_audit():
    b = [rect(0, 0, W, H, C["bg"]), header("audit", admin=True)]
    b.append(page_title("商品审核", "审核卖家提交的商品，通过后公开展示", 112))
    b.append(rect(40, 150, 420, 570, "#FFFFFF", C["border"], rx=14, shadow=True))
    b.append(text(64, 186, "待审核商品", 16, C["text"], 700))
    b.append(badge(330, 166, "12 件", None, 88))
    b.append(field(64, 204, 372, 40, "搜索商品或卖家", "search"))
    items = [("iPad Air 5 64G 蓝色", "卖家 单锦曼 · 10-29 09:12", "g1", "tablet", True),
             ("高等数学教材 第七版", "卖家 张同学 · 10-29 09:30", "g2", "book", False),
             ("索尼 WH-1000XM4 耳机", "卖家 李同学 · 10-29 10:05", "g5", "headphones", False),
             ("捷安特山地自行车", "卖家 王同学 · 10-29 10:42", "g3", "bike", False),
             ("护眼台灯 可调光", "卖家 陈同学 · 10-29 11:18", "g4", "lamp", False)]
    for i, (title, meta, grad, ic, active) in enumerate(items):
        y = 260 + i * 84
        if active:
            b.append(rect(56, y, 388, 74, C["primary_light"], C["primary"], rx=10, sw=1))
        b.append(product_thumb(70, y + 12, 50, 50, grad, ic))
        b.append(text(134, y + 28, title, 13, C["text"], 600))
        b.append(text(134, y + 48, meta, 10, C["muted"]))
        b.append(text(134, y + 64, "待审核", 10, C["warning"], 500))
        b.append(text(390, y + 36, "›", 18, C["subtle"]))

    b.append(rect(480, 150, 846, 570, "#FFFFFF", C["border"], rx=14, shadow=True))
    b.append(text(508, 192, "iPad Air 5 64G 蓝色", 22, C["text"], 700))
    b.append(badge(1180, 170, "待审核"))
    b.append(text(508, 220, "卖家：单锦曼 · 提交时间：2026-10-29 09:12 · 商品 ID：P-2026-1001", 11, C["muted"]))
    for i, (grad, ic) in enumerate([("g1", "tablet"), ("g5", "headphones"), ("g6", "tablet")]):
        b.append(product_thumb(508 + i * 194, 244, 178, 116, grad, ic))
    detail = [("分类", "数码产品"), ("成色", "95 新"), ("价格", "¥ 2,680"),
              ("交易地点", "仙林校区 · 四组团"), ("备注", "含原装充电器和保护壳"), ("版本", "V2 · 2026-10-29")]
    for i, (k, v) in enumerate(detail):
        col, row = i % 3, i // 3
        x = 508 + col * 268
        y = 402 + row * 40
        b.append(text(x, y, k, 11, C["muted"]))
        b.append(text(x + 62, y, v, 12, C["text"], 500))
    b.append(text(508, 486, "审核历史", 13, C["text"], 700))
    history = [("10-28 16:20", "卖家提交 V1 版本", "已通过"),
               ("10-29 09:12", "卖家修改价格并重新提交", "待审核")]
    for i, (tm, action, st) in enumerate(history):
        y = 512 + i * 32
        b.append(circle(516, y - 4, 4, C["primary"] if i == 0 else C["warning"]))
        b.append(text(532, y, tm, 11, C["muted"]))
        b.append(text(630, y, action, 11, C["text"]))
        b.append(badge(1120, y - 10, st))
    b.append(label(508, 590, "驳回原因（驳回时必填）"))
    b.append(rect(508, 598, 790, 46, "#FFFFFF", C["border"], rx=8))
    b.append(text(522, 624, "请填写驳回原因，便于卖家修改后重新提交。", 11, C["subtle"]))
    b.append(button(508, 660, 170, 44, "通过并发布", "success", "check"))
    b.append(button(692, 660, 120, 44, "驳回", "danger"))
    b.append(button(826, 660, 160, 44, "查看历史版本", "secondary", "clock"))
    return svg_doc(W, H, "".join(b))


def screen_admin_complaints():
    b = [rect(0, 0, W, H, C["bg"]), header("complaint", admin=True)]
    b.append(page_title("投诉与申诉", "核实投诉、处置违规商品与账户，并处理申诉", 112))
    tabs = ["待处理投诉", "待处理申诉", "已处理"]
    x = 40
    for i, name in enumerate(tabs):
        active = i == 0
        b.append(text(x, 164, name, 13, C["primary"] if active else C["muted"], 600 if active else 400))
        if active:
            b.append(rect(x, 178, len(name) * 13, 3, C["primary"], rx=2))
        x += len(name) * 13 + 36

    b.append(rect(40, 200, 760, 500, "#FFFFFF", C["border"], rx=14, shadow=True))
    b.append(rect(40, 200, 760, 46, "#F9FAFB", rx=14))
    cols = [("投诉编号", 64), ("投诉对象", 180), ("类型", 360), ("投诉人", 450), ("状态", 540), ("操作", 660)]
    for name, x in cols:
        b.append(text(x, 228, name, 12, C["muted"], 600))
    b.append(line(40, 246, 800, 246, C["border"]))
    rows = [("C-1024", "iPad Air 5 · P-2026-1001", "商品描述不符", "王同学", "待处理", True),
            ("C-1023", "高等数学教材", "疑似盗版", "李同学", "待处理", False),
            ("C-1022", "索尼耳机", "卖家态度恶劣", "张同学", "处理中", False),
            ("C-1021", "捷安特自行车", "虚假成色", "陈同学", "待处理", False),
            ("C-1020", "护眼台灯", "违规物品", "刘同学", "已处理", False)]
    for i, (cid, target, typ, who, st, active) in enumerate(rows):
        y = 246 + i * 82
        if active:
            b.append(rect(52, y + 6, 736, 70, C["primary_light"], C["primary"], rx=10, sw=1))
        b.append(text(64, y + 32, cid, 12, C["text"], 600))
        b.append(text(180, y + 32, target, 12, C["text"]))
        b.append(text(360, y + 32, typ, 12, C["muted"]))
        b.append(text(450, y + 32, who, 12, C["muted"]))
        b.append(badge(540, y + 18, st))
        b.append(text(660, y + 32, "查看", 12, C["primary"], 500))
        b.append(line(64, y + 74, 776, y + 74, C["border"]))

    b.append(rect(820, 200, 506, 500, "#FFFFFF", C["border"], rx=14, shadow=True))
    b.append(text(844, 238, "投诉详情", 16, C["text"], 700))
    b.append(badge(1200, 216, "待处理"))
    b.append(text(844, 270, "C-1024 · 商品描述不符", 13, C["text"], 600))
    b.append(text(844, 292, "投诉人：王同学 · 2026-10-29 10:22", 11, C["muted"]))
    b.append(rect(844, 310, 458, 68, C["gray_light"], rx=10))
    b.append(text(860, 336, "投诉内容", 11, C["muted"], 600))
    b.append(text(860, 358, "卖家描述为 95 新，但实物边框有明显磕碰，要求核实处理。", 11, C["text"]))
    for i, grad in enumerate(["g1", "g5", "g6"]):
        b.append(rect(844 + i * 154, 394, 138, 84, f"url(#{grad})", rx=10))
        b.append(text(844 + i * 154 + 69, 442, "证据图片", 10, "#FFFFFF", 500, "middle"))
    b.append(text(844, 510, "申诉处理", 13, C["text"], 700))
    b.append(text(844, 534, "若被处罚方提交申诉，管理员可选择维持处罚或撤销处罚。", 11, C["muted"]))
    b.append(button(844, 560, 140, 38, "维持处罚", "secondary", size=12))
    b.append(button(996, 560, 140, 38, "撤销处罚", "secondary", size=12))
    b.append(line(844, 620, 1302, 620, C["border"]))
    b.append(button(844, 640, 180, 42, "强制下架商品", "danger", "alert"))
    b.append(button(1038, 640, 120, 42, "冻结账户", "secondary", "lock"))
    b.append(button(1172, 640, 120, 42, "驳回投诉", "ghost"))
    return svg_doc(W, H, "".join(b))


def screen_admin_stats():
    b = [rect(0, 0, W, H, C["bg"]), header("stats", admin=True)]
    b.append(page_title("统计与日志", "查看分类统计、成交趋势和关键操作日志", 112))
    stats = [("128", "商品总数", "未删除商品"), ("46", "累计成交", "成交记录数"),
             ("7", "违规处置", "本月处置"), ("320", "活跃用户", "近 30 天")]
    for i, (num, lab, sub) in enumerate(stats):
        x = 40 + i * 324
        b.append(rect(x, 150, 300, 88, "#FFFFFF", C["border"], rx=14, shadow=True))
        b.append(text(x + 20, 188, num, 26, C["text"], 700))
        b.append(text(x + 20, 212, lab, 13, C["text"], 600))
        b.append(text(x + 20, 228, sub, 11, C["muted"]))

    b.append(rect(40, 258, 620, 250, "#FFFFFF", C["border"], rx=14, shadow=True))
    b.append(text(64, 294, "分类商品数量", 16, C["text"], 700))
    b.append(text(520, 294, "未删除商品", 11, C["muted"]))
    bars = [("数码产品", 32), ("图书", 28), ("生活用品", 24), ("运动", 18), ("其他", 26)]
    for i, (name, value) in enumerate(bars):
        y = 326 + i * 34
        b.append(text(64, y + 5, name, 11, C["muted"]))
        b.append(rect(150, y - 6, 380, 14, C["gray_light"], rx=7))
        b.append(rect(150, y - 6, 380 * value / 40, 14, C["primary"], rx=7))
        b.append(text(548, y + 5, str(value), 11, C["text"], 600))

    b.append(rect(680, 258, 646, 250, "#FFFFFF", C["border"], rx=14, shadow=True))
    b.append(text(704, 294, "成交趋势", 16, C["text"], 700))
    b.append(text(1170, 294, "近 7 天", 11, C["muted"]))
    values = [3, 5, 4, 7, 6, 9, 8]
    labels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    for i in range(5):
        y = 330 + i * 28
        b.append(line(720, y, 1290, y, C["border"]))
    points = []
    for i, v in enumerate(values):
        x = 740 + i * 80
        y = 442 - v * 11
        points.append((x, y))
        b.append(circle(x, y, 4, C["primary"]))
        b.append(text(x, 462, labels[i], 10, C["muted"], 400, "middle"))
    b.append('<polyline points="' + " ".join(f"{x},{y}" for x, y in points) + f'" fill="none" stroke="{C["primary"]}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')
    b.append(text(720, 334, "10", 10, C["subtle"]))
    b.append(text(720, 446, "0", 10, C["subtle"]))

    b.append(rect(40, 530, 1286, 190, "#FFFFFF", C["border"], rx=14, shadow=True))
    b.append(text(64, 566, "操作日志", 16, C["text"], 700))
    b.append(text(980, 566, "时间范围：近 7 天", 11, C["muted"]))
    b.append(button(1120, 548, 90, 32, "筛选", "secondary", "filter", 12))
    b.append(button(1220, 548, 82, 32, "导出", "secondary", size=12))
    b.append(rect(40, 584, 1286, 36, "#F9FAFB", rx=10))
    cols = [("时间", 64), ("操作者", 230), ("动作", 340), ("业务对象", 620), ("结果", 940), ("详情", 1120)]
    for name, x in cols:
        b.append(text(x, 607, name, 11, C["muted"], 600))
    logs = [("10-29 10:12", "王同学", "创建预约", "商品 P-2026-1001", "成功"),
            ("10-29 09:40", "单锦曼", "提交审核", "商品 P-2026-1002", "成功"),
            ("10-29 09:12", "管理员 A", "审核通过", "商品 P-2026-1002", "成功"),
            ("10-29 08:55", "管理员 B", "强制下架", "商品 P-2026-0988", "成功")]
    for i, (tm, who, action, target, result) in enumerate(logs):
        y = 632 + i * 22
        b.append(text(64, y, tm, 11, C["muted"]))
        b.append(text(230, y, who, 11, C["text"]))
        b.append(text(340, y, action, 11, C["text"]))
        b.append(text(620, y, target, 11, C["muted"]))
        b.append(text(940, y, result, 11, C["success"], 500))
        b.append(text(1120, y, "查看", 11, C["primary"], 500))
    return svg_doc(W, H, "".join(b))


def mobile_header(title, back=True):
    out = [rect(0, 0, 375, 56, "#FFFFFF"), line(0, 56, 375, 56, C["border"])]
    if back:
        out.append(icon("arrow_left", 18, 18, 20, C["text"]))
    out.append(text(187, 35, title, 16, C["text"], 700, "middle"))
    out.append(icon("more", 338, 18, 20, C["muted"]))
    return "".join(out)


def screen_mobile_products():
    w, h = 375, 812
    b = [rect(0, 0, w, h, C["bg"])]
    b.append(rect(0, 0, w, 56, "#FFFFFF"))
    b.append(text(20, 35, "校园二手", 18, C["text"], 700))
    b.append(icon("search", 278, 18, 20, C["muted"]))
    b.append(icon("bell", 328, 18, 20, C["muted"]))
    b.append(line(0, 56, w, 56, C["border"]))
    b.append(field(16, 68, 343, 40, "搜索商品名称或描述", "search"))
    chips = ["全部", "数码", "图书", "生活", "运动"]
    x = 16
    for i, name in enumerate(chips):
        cw = 54 if len(name) <= 2 else 60
        b.append(rect(x, 120, cw, 28, C["primary"] if i == 0 else "#FFFFFF", C["primary"] if i == 0 else C["border"], rx=14))
        b.append(text(x + cw / 2, 139, name, 11, "#FFFFFF" if i == 0 else C["muted"], 500, "middle"))
        x += cw + 8

    items = [
        ("iPad Air 5", "¥ 2,680", "仙林", "g1", "tablet"),
        ("高数教材", "¥ 25", "鼓楼", "g2", "book"),
        ("山地自行车", "¥ 680", "仙林", "g3", "bike"),
        ("索尼耳机", "¥ 1,150", "仙林", "g5", "headphones"),
        ("护眼台灯", "¥ 45", "鼓楼", "g4", "lamp"),
        ("斯伯丁篮球", "¥ 80", "仙林", "g6", "ball"),
    ]
    for i, (title, price, loc, grad, ic) in enumerate(items):
        col, row = i % 2, i // 2
        x = 16 + col * 180
        y = 160 + row * 190
        b.append(rect(x, y, 163, 178, "#FFFFFF", C["border"], rx=12, shadow=True))
        b.append(product_thumb(x + 8, y + 8, 147, 92, grad, ic))
        b.append(text(x + 10, y + 122, title, 12, C["text"], 600))
        b.append(text(x + 10, y + 146, price, 16, C["primary"], 700))
        b.append(text(x + 10, y + 166, loc + "校区", 10, C["muted"]))
        b.append(badge(x + 104, y + 16, "在售", "已发布", 48))

    b.append(rect(0, 752, w, 60, "#FFFFFF"))
    b.append(line(0, 752, w, 752, C["border"]))
    nav = [("home", "首页", False), ("box", "商品", True), ("calendar", "预约", False), ("user", "我的", False)]
    for i, (ic, name, active) in enumerate(nav):
        x = 47 + i * 94
        b.append(icon(ic, x - 10, 764, 20, C["primary"] if active else C["subtle"]))
        b.append(text(x, 800, name, 10, C["primary"] if active else C["muted"], 600 if active else 400, "middle"))
    return svg_doc(w, h, "".join(b))


def screen_mobile_detail():
    w, h = 375, 812
    b = [rect(0, 0, w, h, C["bg"]), mobile_header("商品详情")]
    b.append(product_thumb(0, 56, 375, 260, "g1", "tablet", "数码产品"))
    b.append(rect(0, 292, 375, 440, "#FFFFFF", rx=18))
    b.append(text(20, 338, "iPad Air 5 64G 蓝色", 20, C["text"], 700))
    b.append(text(20, 374, "¥ 2,680", 26, C["primary"], 700))
    b.append(badge(300, 322, "已发布"))
    b.append(text(20, 404, "95 新 · 仙林校区 · 10-28 发布", 11, C["muted"]))
    b.append(line(20, 424, 355, 424, C["border"]))
    b.append(avatar(20, 444, 36, "李", C["success"]))
    b.append(text(66, 458, "李同学", 13, C["text"], 600))
    b.append(text(66, 476, "信用 98 · 在售 3 件", 10, C["muted"]))
    b.append(text(270, 458, "查看主页  ›", 11, C["primary"], 500))
    b.append(text(20, 514, "商品描述", 14, C["text"], 700))
    b.append(multiline(20, 540, [
        "自用 iPad Air 5，64G，蓝色，无磕碰，电池健康 92%。",
        "含原装充电器和保护壳。因换新出售，可在仙林校区当面验机。",
    ], 11, C["muted"], 400, 20))
    b.append(text(20, 606, "交易提示", 14, C["text"], 700))
    b.append(multiline(20, 632, [
        "预约成功即锁定商品，先到先得。",
        "线下交易请当面验货；双方确认后成交不可撤销。",
    ], 11, C["muted"], 400, 20))
    b.append(rect(0, 732, w, 80, "#FFFFFF"))
    b.append(line(0, 732, w, 732, C["border"]))
    b.append(text(20, 762, "¥ 2,680", 18, C["primary"], 700))
    b.append(text(20, 782, "预约后锁定商品", 10, C["muted"]))
    b.append(button(170, 748, 90, 44, "联系卖家", "secondary", size=12))
    b.append(button(272, 748, 84, 44, "立即预约", "primary", size=12))
    return svg_doc(w, h, "".join(b))
