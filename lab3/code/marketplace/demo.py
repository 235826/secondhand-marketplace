"""显式生成纯虚构演示数据；不覆盖已有账号，不在普通启动时执行。"""

import io
import secrets

from PIL import Image, ImageDraw

from .accounts import password_hash
from .domain import require
from .products import ProductService

DEMO_PASSWORD = "Campus-demo-2026"


def seed_demo(database, accounts, image_dir, count=8, buyer_count=3):
    require(8 <= count <= 10000 and 3 <= buyer_count <= 100, "演示数据规模无效", 400)
    require(
        not database.one("SELECT 1 FROM users WHERE email='demo-seller@nju.edu.cn'"),
        "演示数据已经存在；请另建 instance，避免覆盖已有数据",
    )
    admin = database.one("SELECT id FROM users WHERE role='INITIAL_ADMIN'")
    require(admin, "请先创建初始管理员")
    encoded = password_hash(DEMO_PASSWORD)
    import time

    with database.transaction(admin["id"], "SEED_DEMO") as db:
        seller = db.execute(
            "INSERT INTO users(email,nickname,password_hash,role,created_at) "
            "VALUES('demo-seller@nju.edu.cn','林同学',?,'USER',?)",
            (encoded, time.time()),
        ).lastrowid
        buyers = []
        for index in range(buyer_count):
            buyers.append(
                db.execute(
                    "INSERT INTO users(email,nickname,password_hash,role,created_at) "
                    "VALUES(?,?,?,'USER',?)",
                    (f"demo-buyer{index + 1}@nju.edu.cn", f"同学{index + 1}", encoded, time.time()),
                ).lastrowid
            )
    products = ProductService(database, image_dir)
    palette = [
        ("#dceaff", "#719ce0"),
        ("#fce3ee", "#d390ac"),
        ("#e1f3e8", "#77af91"),
        ("#eee5ff", "#ac91d0"),
        ("#fff0cf", "#c5a05f"),
    ]
    images = []
    for index, (background, accent) in enumerate(palette):
        image = Image.new("RGB", (800, 560), background)
        draw = ImageDraw.Draw(image)
        draw.ellipse((190, 70, 610, 490), fill=accent)
        if index == 1:
            draw.rounded_rectangle((280, 130, 520, 430), radius=12, fill="white")
            draw.rectangle((300, 165, 315, 395), fill=accent)
            for y in (210, 245, 280):
                draw.rounded_rectangle((345, y, 475, y + 8), radius=3, fill=accent)
        elif index == 2:
            draw.ellipse((230, 265, 370, 405), outline="white", width=12)
            draw.ellipse((430, 265, 570, 405), outline="white", width=12)
            draw.line(
                [(300, 335), (370, 230), (500, 335), (300, 335), (405, 335), (370, 230)],
                fill="white",
                width=10,
            )
            draw.line([(470, 205), (500, 335)], fill="white", width=10)
        elif index == 4:
            draw.polygon([(350, 145), (450, 145), (510, 300), (290, 300)], fill="white")
            draw.rectangle((392, 300, 408, 405), fill="white")
            draw.rounded_rectangle((335, 400, 465, 415), radius=7, fill="white")
        else:
            draw.rounded_rectangle((290, 125, 510, 430), radius=22, fill="white")
            draw.rounded_rectangle((305, 145, 495, 400), radius=12, fill=background)
            draw.ellipse((390, 408, 410, 428), fill=accent)
        buffer = io.BytesIO()
        image.save(buffer, "PNG")
        images.append(products.upload(seller, buffer.getvalue()))
    goods = [
        ("iPad Air 5 蓝色 · 含保护壳", "2680", 1),
        ("高等数学教材 第七版", "25", 2),
        ("校园通勤自行车", "380", 4),
        ("平板阅读器 64G", "450", 1),
        ("护眼台灯 可调光", "45", 3),
        ("数据结构与算法教材", "32", 2),
        ("宿舍收纳用品", "18", 3),
        ("运动背包 九成新", "65", 4),
    ]
    ids = []
    for index in range(count):
        title, price, category = goods[index % len(goods)]
        if count > 8:
            title = f"{title} · {index + 1}"
        data = dict(
            title=title,
            description="自用闲置，功能完好。支持当面检查，喜欢的同学欢迎预约。",
            category_id=category,
            price=price,
            condition="九成新",
            location="仙林校区 · 食堂门口",
            note="面交时间可在预约留言中协商。",
            image_keys=[images[index % len(images)]],
        )
        pid = products.save(seller, data, secrets.token_hex(16), submit=True)
        item = products.detail(pid, seller)
        products.review(admin["id"], pid, item["current_version_id"], item["revision"], True)
        ids.append(pid)
    return dict(seller=seller, buyers=buyers, products=ids)
