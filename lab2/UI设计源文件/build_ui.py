#!/usr/bin/env python3
import os
import subprocess

from generate_ui import SVG_DIR, PNG_DIR, screen_login, screen_products, screen_detail
from screens_extra import (
    screen_seller_products,
    screen_edit_product,
    screen_seller_reservations,
    screen_buyer_reservations,
    screen_admin_audit,
    screen_admin_complaints,
    screen_admin_stats,
    screen_mobile_products,
    screen_mobile_detail,
)

SCREENS = [
    ("01-登录注册", screen_login),
    ("02-商品列表与筛选", screen_products),
    ("03-商品详情与预约", screen_detail),
    ("04-卖家商品管理", screen_seller_products),
    ("05-商品编辑与送审", screen_edit_product),
    ("06-卖家预约与候补管理", screen_seller_reservations),
    ("07-买家我的预约与成交确认", screen_buyer_reservations),
    ("08-管理员商品审核台", screen_admin_audit),
    ("09-管理员投诉申诉与账户处置", screen_admin_complaints),
    ("10-管理员统计与日志", screen_admin_stats),
    ("11-移动端商品列表", screen_mobile_products),
    ("12-移动端商品详情", screen_mobile_detail),
]


def main():
    for name, fn in SCREENS:
        svg = fn()
        svg_path = os.path.join(SVG_DIR, name + ".svg")
        png_path = os.path.join(PNG_DIR, name + ".png")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg)
        subprocess.run(["rsvg-convert", svg_path, "-o", png_path], check=True)
        print("generated", png_path)


if __name__ == "__main__":
    main()
