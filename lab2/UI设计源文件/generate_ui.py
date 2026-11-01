#!/usr/bin/env python3
import os
import subprocess
from html import escape

BASE = os.path.dirname(os.path.abspath(__file__))
SVG_DIR = os.path.join(BASE, "svg")
PNG_DIR = os.path.abspath(os.path.join(BASE, "..", "UI界面"))
os.makedirs(SVG_DIR, exist_ok=True)
os.makedirs(PNG_DIR, exist_ok=True)

W, H = 1366, 768
FONT = "PingFang SC, Hiragino Sans GB, Arial, sans-serif"

C = {
    "bg": "#F4F6FB",
    "card": "#FFFFFF",
    "text": "#111827",
    "muted": "#6B7280",
    "subtle": "#9CA3AF",
    "border": "#E5E7EB",
    "primary": "#2563EB",
    "primary_dark": "#1D4ED8",
    "primary_light": "#EFF6FF",
    "success": "#16A34A",
    "success_light": "#DCFCE7",
    "warning": "#D97706",
    "warning_light": "#FEF3C7",
    "danger": "#DC2626",
    "danger_light": "#FEE2E2",
    "purple": "#7C3AED",
    "purple_light": "#EDE9FE",
    "gray_light": "#F3F4F6",
}

DEFS = """
<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
  <feDropShadow dx="0" dy="2" stdDeviation="8" flood-color="#0F172A" flood-opacity="0.08"/>
</filter>
<linearGradient id="gBrand" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#1D4ED8"/><stop offset="1" stop-color="#60A5FA"/>
</linearGradient>
<linearGradient id="g1" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#DBEAFE"/><stop offset="1" stop-color="#93C5FD"/>
</linearGradient>
<linearGradient id="g2" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#FCE7F3"/><stop offset="1" stop-color="#F9A8D4"/>
</linearGradient>
<linearGradient id="g3" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#DCFCE7"/><stop offset="1" stop-color="#86EFAC"/>
</linearGradient>
<linearGradient id="g4" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#FEF3C7"/><stop offset="1" stop-color="#FCD34D"/>
</linearGradient>
<linearGradient id="g5" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#EDE9FE"/><stop offset="1" stop-color="#C4B5FD"/>
</linearGradient>
<linearGradient id="g6" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#E0F2FE"/><stop offset="1" stop-color="#7DD3FC"/>
</linearGradient>
"""

ICONS = {
    "search": "M21 21l-4.35-4.35M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15z",
    "bell": "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0",
    "user": "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
    "home": "M3 11l9-8 9 8M5 10v10h14V10",
    "box": "M21 8l-9-5-9 5 9 5 9-5zM3 8v8l9 5 9-5V8M12 13v8",
    "calendar": "M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z",
    "check": "M20 6L9 17l-5-5",
    "shield": "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
    "chart": "M3 3v18h18M7 14l3-3 3 2 4-5",
    "flag": "M4 22V4M4 4h12l-2 4 2 4H4",
    "chevron_down": "M6 9l6 6 6-6",
    "arrow_right": "M5 12h14M13 6l6 6-6 6",
    "arrow_left": "M19 12H5M11 18l-6-6 6-6",
    "plus": "M12 5v14M5 12h14",
    "edit": "M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z",
    "eye": "M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z",
    "lock": "M7 11V7a5 5 0 0 1 10 0v4M5 11h14v11H5z",
    "mail": "M4 4h16v16H4zM4 6l8 7 8-7",
    "filter": "M3 5h18M6 12h12M10 19h4",
    "star": "M12 2l3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1 3-6z",
    "clock": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM12 6v6l4 2",
    "alert": "M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z",
    "more": "M12 13a1 1 0 1 0 0-2 1 1 0 0 0 0 2zM19 13a1 1 0 1 0 0-2 1 1 0 0 0 0 2zM5 13a1 1 0 1 0 0-2 1 1 0 0 0 0 2z",
    "book": "M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 19.5A2.5 2.5 0 0 0 6.5 22H20V2H6.5A2.5 2.5 0 0 0 4 4.5v15z",
    "headphones": "M3 18v-6a9 9 0 0 1 18 0v6M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3v5zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3v5z",
    "bike": "M5.5 20a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM18.5 20a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM5.5 16.5L9 9h6l3.5 7.5M9 9l3 7.5H5.5",
    "lamp": "M8 2h8l4 12H4L8 2zM12 14v8M8 22h8",
    "tablet": "M7 2h10a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zM11 18h2",
    "ball": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM12 7v10M7 12h10",
}


def e(s):
    return escape(str(s))


def text(x, y, s, size=14, color=None, weight=400, anchor="start", opacity=1, spacing=None):
    color = color or C["text"]
    attrs = (
        f'x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
        f'fill="{color}" font-weight="{weight}" text-anchor="{anchor}"'
    )
    if opacity != 1:
        attrs += f' opacity="{opacity}"'
    if spacing is not None:
        attrs += f' letter-spacing="{spacing}"'
    return f"<text {attrs}>{e(s)}</text>"


def multiline(x, y, lines, size=14, color=None, weight=400, line_height=22, anchor="start"):
    out = []
    for i, line in enumerate(lines):
        out.append(text(x, y + i * line_height, line, size, color, weight, anchor))
    return "".join(out)


def rect(x, y, w, h, fill="#FFFFFF", stroke="none", rx=0, shadow=False, opacity=1, sw=1):
    filt = ' filter="url(#shadow)"' if shadow else ""
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}"{filt}/>'
    )


def line(x1, y1, x2, y2, color=None, width=1, dash=None):
    color = color or C["border"]
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{d}/>'


def circle(cx, cy, r, fill="none", stroke="none", width=1, opacity=1):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}"/>'


def icon(name, x, y, size=20, color=None, sw=2):
    d = ICONS[name]
    return (
        f'<g transform="translate({x},{y}) scale({size / 24})">'
        f'<path d="{d}" fill="none" stroke="{color or C["muted"]}" stroke-width="{sw}" '
        f'stroke-linecap="round" stroke-linejoin="round"/></g>'
    )


def avatar(x, y, size, label, bg=None):
    bg = bg or C["primary"]
    return circle(x + size / 2, y + size / 2, size / 2, bg) + text(
        x + size / 2, y + size / 2 + size * 0.15, label, size * 0.38, "#FFFFFF", 600, "middle"
    )


STATUS = {
    "草稿": ("#F3F4F6", C["muted"]),
    "待审核": (C["warning_light"], C["warning"]),
    "已发布": (C["success_light"], C["success"]),
    "已预约": (C["primary_light"], C["primary"]),
    "已下架": ("#F3F4F6", C["muted"]),
    "已成交": (C["purple_light"], C["purple"]),
    "违规封禁": (C["danger_light"], C["danger"]),
    "待卖家确认": (C["warning_light"], C["warning"]),
    "待成交": (C["primary_light"], C["primary"]),
    "已完成": (C["success_light"], C["success"]),
    "已取消": ("#F3F4F6", C["muted"]),
    "待处理": (C["warning_light"], C["warning"]),
    "处理中": (C["primary_light"], C["primary"]),
    "已处理": (C["success_light"], C["success"]),
    "候补中": (C["purple_light"], C["purple"]),
    "已通过": (C["success_light"], C["success"]),
    "已驳回": (C["danger_light"], C["danger"]),
}


def badge(x, y, label, kind=None, width=None):
    fill, color = STATUS.get(kind or label, (C["gray_light"], C["muted"]))
    w = width or max(62, len(label) * 14 + 22)
    return rect(x, y, w, 24, fill, rx=12) + text(x + w / 2, y + 16, label, 12, color, 600, "middle")


def button(x, y, w, h, label, kind="primary", icon_name=None, size=14):
    if kind == "primary":
        fill, stroke, color = C["primary"], "none", "#FFFFFF"
    elif kind == "secondary":
        fill, stroke, color = "#FFFFFF", C["border"], C["text"]
    elif kind == "ghost":
        fill, stroke, color = "none", "none", C["primary"]
    elif kind == "danger":
        fill, stroke, color = C["danger_light"], "none", C["danger"]
    elif kind == "success":
        fill, stroke, color = C["success"], "none", "#FFFFFF"
    else:
        fill, stroke, color = C["gray_light"], "none", C["text"]
    out = rect(x, y, w, h, fill, stroke, rx=8)
    if icon_name:
        icon_size = 16
        content_w = icon_size + 8 + len(label) * size
        ix = x + (w - content_w) / 2
        out += icon(icon_name, ix, y + (h - icon_size) / 2, icon_size, color)
        out += text(ix + icon_size + 8, y + h / 2 + 5, label, size, color, 600)
    else:
        out += text(x + w / 2, y + h / 2 + 5, label, size, color, 600, "middle")
    return out


def field(x, y, w, h, placeholder, icon_name=None, value=None, muted_placeholder=True):
    out = rect(x, y, w, h, "#FFFFFF", C["border"], rx=8)
    tx = x + 14
    if icon_name:
        out += icon(icon_name, x + 14, y + (h - 18) / 2, 18, C["subtle"])
        tx = x + 42
    label = value if value is not None else placeholder
    color = C["text"] if value is not None else C["subtle"]
    out += text(tx, y + h / 2 + 5, label, 13, color, 400)
    return out


def label(x, y, s):
    return text(x, y, s, 12, C["muted"], 600)


def header(active, admin=False):
    out = [rect(0, 0, W, 64, "#FFFFFF"), line(0, 64, W, 64, C["border"])]
    out.append(rect(28, 14, 36, 36, C["primary"], rx=10))
    out.append(text(46, 39, "二", 18, "#FFFFFF", 700, "middle"))
    out.append(text(76, 37, "南大二手", 20, C["text"], 700))
    out.append(text(76, 53, "校园二手交易", 11, C["muted"]))

    if admin:
        items = [("audit", "商品审核"), ("complaint", "投诉申诉"), ("stats", "统计日志"), ("accounts", "账户管理")]
    else:
        items = [("home", "首页"), ("products", "商品"), ("reservations", "我的预约"), ("seller", "卖家中心")]

    x = 260
    for key, name in items:
        is_active = key == active
        out.append(text(x, 39, name, 14, C["primary"] if is_active else C["muted"], 600 if is_active else 400))
        if is_active:
            out.append(rect(x, 60, len(name) * 14, 3, C["primary"], rx=2))
        x += len(name) * 14 + 38

    out.append(icon("search", 1050, 22, 20, C["muted"]))
    out.append(icon("bell", 1100, 22, 20, C["muted"]))
    out.append(avatar(1158, 16, 32, "管" if admin else "单", C["purple"] if admin else C["primary"]))
    out.append(text(1200, 35, "管理员" if admin else "单锦曼", 13, C["text"], 600))
    out.append(text(1200, 51, "平台管理员" if admin else "普通用户", 11, C["muted"]))
    return "".join(out)


def page_title(title, subtitle="", y=112, right=None):
    out = [text(40, y, title, 28, C["text"], 700)]
    if subtitle:
        out.append(text(40, y + 26, subtitle, 14, C["muted"]))
    if right:
        out.append(right)
    return "".join(out)


def product_thumb(x, y, w, h, grad, icon_name, label_text=None):
    out = [rect(x, y, w, h, f"url(#{grad})", rx=12)]
    out.append(circle(x + w / 2, y + h / 2 - 4, min(w, h) * 0.22, "#FFFFFF", opacity=0.35))
    out.append(icon(icon_name, x + w / 2 - min(w, h) * 0.16, y + h / 2 - min(w, h) * 0.2, min(w, h) * 0.32, "#FFFFFF", 1.6))
    if label_text:
        out.append(text(x + w / 2, y + h - 12, label_text, 11, "#FFFFFF", 600, "middle"))
    return "".join(out)


def card(x, y, w, h, title=None, subtitle=None):
    out = [rect(x, y, w, h, "#FFFFFF", C["border"], rx=14, shadow=True)]
    if title:
        out.append(text(x + 24, y + 36, title, 17, C["text"], 700))
    if subtitle:
        out.append(text(x + 24, y + 58, subtitle, 12, C["muted"]))
    return "".join(out)


def svg_doc(w, h, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f"<defs>{DEFS}</defs>{body}</svg>"
    )


def screen_login():
    b = [rect(0, 0, W, H, C["bg"])]
    b.append(rect(0, 0, 760, H, "url(#gBrand)"))
    b.append(circle(660, 120, 200, "#FFFFFF", opacity=0.08))
    b.append(circle(720, 610, 260, "#FFFFFF", opacity=0.05))
    b.append(circle(120, 690, 160, "#FFFFFF", opacity=0.05))
    b.append(rect(72, 58, 36, 36, "#FFFFFF", rx=10))
    b.append(text(90, 83, "二", 18, C["primary"], 700, "middle"))
    b.append(text(120, 82, "南大二手", 20, "#FFFFFF", 700))
    b.append(text(120, 100, "南京大学校园二手交易平台", 11, "#FFFFFF", 400, opacity=0.75))
    b.append(multiline(72, 220, ["让闲置", "重新流动起来"], 42, "#FFFFFF", 700, 54))
    b.append(text(72, 350, "线上预约 · 线下交易 · 双方确认成交", 16, "#FFFFFF", 400, opacity=0.82))
    b.append(text(72, 382, "面向南京大学学生的可信二手交易空间。", 14, "#FFFFFF", 400, opacity=0.68))
    for i, (num, lab) in enumerate([("500+", "在售商品"), ("20", "并发用户"), ("95%", "3 秒内响应")]):
        x = 72 + i * 190
        b.append(rect(x, 470, 168, 78, "#FFFFFF", rx=14, opacity=0.12))
        b.append(text(x + 20, 505, num, 24, "#FFFFFF", 700))
        b.append(text(x + 20, 528, lab, 12, "#FFFFFF", 400, opacity=0.75))
    b.append(text(72, 708, "南京大学 · 校园二手交易系统", 12, "#FFFFFF", 400, opacity=0.55))

    b.append(text(1170, 40, "帮助中心", 12, C["muted"]))
    b.append(rect(830, 112, 470, 560, "#FFFFFF", C["border"], rx=18, shadow=True))
    b.append(text(870, 170, "欢迎回来", 28, C["text"], 700))
    b.append(text(870, 197, "使用南京大学学校邮箱登录", 13, C["muted"]))
    b.append(text(870, 248, "登录", 15, C["primary"], 700))
    b.append(rect(870, 258, 34, 3, C["primary"], rx=2))
    b.append(text(916, 248, "注册", 15, C["muted"], 400))
    b.append(label(870, 298, "学校邮箱"))
    b.append(field(870, 306, 390, 46, "name@smail.nju.edu.cn", "mail"))
    b.append(label(870, 376, "密码"))
    b.append(field(870, 384, 390, 46, "请输入密码", "lock"))
    b.append(rect(870, 448, 18, 18, "#FFFFFF", C["border"], rx=4))
    b.append(text(896, 462, "记住我", 12, C["muted"]))
    b.append(text(1150, 462, "忘记密码？", 12, C["primary"], 500))
    b.append(button(870, 490, 390, 48, "登录", "primary"))
    b.append(line(870, 566, 1260, 566, C["border"]))
    b.append(text(1065, 589, "或", 12, C["subtle"], 400, "middle"))
    b.append(button(870, 610, 390, 46, "注册新账户", "secondary"))
    b.append(text(870, 676, "仅支持南京大学学校邮箱注册；管理员请使用管理员入口。", 11, C["subtle"]))
    b.append(text(870, 694, "登录即表示同意《校园二手交易公约》", 11, C["subtle"]))
    return svg_doc(W, H, "".join(b))


def screen_products():
    b = [rect(0, 0, W, H, C["bg"]), header("products")]
    b.append(page_title("发现好物", "南京大学校园内的闲置交易", 112, button(1170, 96, 156, 42, "发布商品", "primary", "plus")))
    b.append(rect(40, 158, 1286, 94, "#FFFFFF", C["border"], rx=14, shadow=True))
    b.append(field(60, 184, 360, 44, "搜索商品名称或描述", "search"))
    b.append(field(438, 184, 150, 44, "全部分类", "chevron_down"))
    b.append(field(606, 184, 130, 44, "最低价"))
    b.append(text(746, 212, "—", 13, C["subtle"]))
    b.append(field(764, 184, 130, 44, "最高价"))
    b.append(field(912, 184, 140, 44, "全部状态", "chevron_down"))
    b.append(field(1070, 184, 130, 44, "最新发布", "chevron_down"))
    b.append(button(1218, 184, 88, 44, "搜索", "primary", "search"))
    b.append(text(60, 236, "热门：iPad　教材　自行车　台灯", 11, C["subtle"]))
    b.append(text(1110, 236, "重置筛选", 11, C["primary"], 500))

    items = [
        ("iPad Air 5 64G 蓝色", "¥ 2,680", "95新", "仙林校区", "已发布", "g1", "tablet", "数码"),
        ("高等数学教材 第七版", "¥ 25", "9成新", "鼓楼校区", "已发布", "g2", "book", "图书"),
        ("捷安特山地自行车", "¥ 680", "8成新", "仙林校区", "已预约", "g3", "bike", "运动"),
        ("索尼 WH-1000XM4 耳机", "¥ 1,150", "95新", "仙林校区", "已发布", "g5", "headphones", "数码"),
        ("护眼台灯 可调光", "¥ 45", "9成新", "鼓楼校区", "已下架", "g4", "lamp", "生活"),
        ("斯伯丁篮球 7 号", "¥ 80", "8成新", "仙林校区", "已成交", "g6", "ball", "运动"),
    ]
    for i, (title, price, cond, loc, status, grad, ic, cat) in enumerate(items):
        col, row = i % 4, i // 4
        x = 40 + col * 326
        y = 278 + row * 226
        b.append(rect(x, y, 306, 210, "#FFFFFF", C["border"], rx=14, shadow=True))
        b.append(product_thumb(x + 12, y + 12, 282, 116, grad, ic, cat))
        b.append(badge(x + 220, y + 20, status))
        b.append(text(x + 16, y + 152, title, 14, C["text"], 600))
        b.append(text(x + 16, y + 178, price, 19, C["primary"], 700))
        b.append(text(x + 16, y + 198, f"{cond} · {loc}", 11, C["muted"]))
        b.append(icon("clock", x + 250, y + 188, 14, C["subtle"]))
        b.append(text(x + 268, y + 198, "10-28", 10, C["subtle"]))

    b.append(text(40, 738, "共 128 件商品", 12, C["muted"]))
    for i, page in enumerate(["1", "2", "3", "…", "13"]):
        x = 1130 + i * 34
        fill = C["primary"] if page == "1" else "#FFFFFF"
        color = "#FFFFFF" if page == "1" else C["muted"]
        b.append(rect(x, 724, 28, 28, fill, C["border"], rx=7))
        b.append(text(x + 14, 743, page, 11, color, 600, "middle"))
    return svg_doc(W, H, "".join(b))


def screen_detail():
    b = [rect(0, 0, W, H, C["bg"]), header("products")]
    b.append(text(40, 98, "首页  /  商品  /  商品详情", 12, C["muted"]))
    b.append(rect(40, 120, 760, 444, "#FFFFFF", C["border"], rx=16, shadow=True))
    b.append(product_thumb(60, 140, 720, 330, "g1", "tablet", "数码产品"))
    for i, grad in enumerate(["g1", "g2", "g3", "g5"]):
        b.append(rect(60 + i * 90, 486, 76, 58, f"url(#{grad})", rx=8))
        if i == 0:
            b.append(rect(58, 484, 80, 62, "none", C["primary"], rx=9, sw=2))

    b.append(rect(830, 120, 496, 444, "#FFFFFF", C["border"], rx=16, shadow=True))
    b.append(text(858, 166, "iPad Air 5 64G 蓝色", 24, C["text"], 700))
    b.append(text(858, 206, "¥ 2,680", 30, C["primary"], 700))
    b.append(badge(1188, 148, "已发布"))
    b.append(line(858, 228, 1298, 228, C["border"]))
    meta = [("分类", "数码产品"), ("成色", "95 新"), ("交易地点", "仙林校区 · 四组团"), ("发布时间", "2026-10-28 14:20")]
    for i, (k, v) in enumerate(meta):
        y = 256 + i * 32
        b.append(text(858, y, k, 12, C["muted"]))
        b.append(text(940, y, v, 13, C["text"], 500))
    b.append(rect(858, 392, 440, 62, C["gray_light"], rx=10))
    b.append(avatar(874, 405, 36, "李", C["success"]))
    b.append(text(922, 416, "李同学", 13, C["text"], 600))
    b.append(text(922, 434, "信用 98 · 在售 3 件", 11, C["muted"]))
    b.append(text(1240, 416, "查看主页", 11, C["primary"], 500))
    b.append(button(858, 474, 214, 48, "立即预约", "primary", "calendar"))
    b.append(button(1084, 474, 214, 48, "联系卖家", "secondary", "user"))
    b.append(text(858, 542, "预约成功即锁定商品，先到先得；取消后释放锁定。", 11, C["warning"]))

    b.append(rect(40, 584, 760, 150, "#FFFFFF", C["border"], rx=16, shadow=True))
    b.append(text(64, 616, "商品描述", 15, C["text"], 700))
    b.append(multiline(64, 644, [
        "自用 iPad Air 5，64G，蓝色，无磕碰，电池健康 92%。含原装充电器和保护壳。",
        "因换新出售，可在仙林校区当面验机。价格可小刀，非诚勿扰。",
    ], 13, C["muted"], 400, 24))
    b.append(rect(830, 584, 496, 150, "#FFFFFF", C["border"], rx=16, shadow=True))
    b.append(text(854, 616, "交易提示", 15, C["text"], 700))
    b.append(multiline(854, 644, [
        "线下交易请当面验货，确认商品无误。",
        "平台不提供在线支付和物流服务。",
        "双方均确认成交后，交易不可撤销。",
    ], 12, C["muted"], 400, 22))
    return svg_doc(W, H, "".join(b))
