"""独立 Chromium 端到端验收；仅用于本地虚构演示数据。"""

import argparse
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

PASSWORD = "Campus-demo-2026"


def login(page, base, email, password=PASSWORD):
    page.goto(base + "/auth/login")
    page.get_by_label("学校邮箱", exact=True).fill(email)
    page.get_by_label("密码", exact=True).fill(password)
    page.get_by_role("button", name="登录", exact=True).click()
    expect(page.get_by_role("heading", name="发现校园好物")).to_be_visible()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:5001")
    parser.add_argument("--chromium", help="可选：已有 Chromium 可执行文件")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    errors, checks = [], []
    with sync_playwright() as playwright:
        options = {"headless": True}
        if args.chromium:
            options["executable_path"] = args.chromium
        browser = playwright.chromium.launch(**options)
        for label, width, height, product_id in (
            ("desktop", 1366, 768, 1),
            ("mobile", 375, 812, 2),
        ):
            context = browser.new_context(viewport={"width": width, "height": height})
            buyer = context.new_page()
            buyer.on("pageerror", lambda error: errors.append(str(error)))
            buyer.goto(args.base)
            expect(buyer.get_by_role("heading", name="发现校园好物")).to_be_visible()
            buyer.screenshot(path=str(args.output / f"{label}-products.png"), full_page=True)
            assert buyer.evaluate("document.documentElement.scrollWidth <= innerWidth")
            login(buyer, args.base, "demo-buyer1@nju.edu.cn")
            buyer.goto(args.base + f"/products/{product_id}")
            title = buyer.locator(".detail h1").inner_text()
            buyer.screenshot(path=str(args.output / f"{label}-detail.png"), full_page=True)
            buyer.get_by_role("button", name="立即预约", exact=True).click()
            card = buyer.locator(".booking").filter(has_text=title).first
            expect(card.locator(".badge")).to_have_text("等待卖家确认")
            card.get_by_role("button", name="取消 / 拒绝预约", exact=True).click()
            expect(
                buyer.locator(".booking").filter(has_text=title).first.locator(".badge")
            ).to_have_text("已取消")
            buyer.goto(args.base + f"/products/{product_id}")
            buyer.get_by_role("button", name="立即预约", exact=True).click()
            seller_context = browser.new_context(viewport={"width": width, "height": height})
            seller = seller_context.new_page()
            login(seller, args.base, "demo-seller@nju.edu.cn")
            seller.goto(args.base + "/bookings")
            seller.locator(".booking").filter(has_text=title).first.get_by_role(
                "button", name="确认预约", exact=True
            ).click()
            buyer.reload()
            buyer.locator(".booking").filter(has_text=title).first.get_by_role(
                "link", name="面交留言与历史记录 →"
            ).click()
            buyer.get_by_label("面交留言").fill("明天下午在食堂门口面交。")
            buyer.get_by_role("button", name="发送留言", exact=True).click()
            buyer.locator(".booking").filter(has_text=title).first.get_by_role(
                "button", name="已完成面交，确认成交", exact=True
            ).click()
            expect(
                buyer.locator(".booking").filter(has_text=title).first.locator(".badge")
            ).to_have_text("卖家已确认预约")
            seller.reload()
            seller.locator(".booking").filter(has_text=title).first.get_by_role(
                "button", name="已完成面交，确认成交", exact=True
            ).click()
            buyer.reload()
            expect(
                buyer.locator(".booking").filter(has_text=title).first.locator(".badge")
            ).to_have_text("已成交")
            assert buyer.evaluate("document.documentElement.scrollWidth <= innerWidth")
            buyer.screenshot(path=str(args.output / f"{label}-completed.png"), full_page=True)
            checks.append(
                {
                    "viewport": [width, height],
                    "flow": "登录→详情→预约→取消→再预约→卖家确认→留言→双方成交",
                    "passed": True,
                }
            )
            seller_context.close()
            context.close()
        admin_context = browser.new_context(viewport={"width": 1366, "height": 768})
        page = admin_context.new_page()
        login(page, args.base, "admin@nju.edu.cn", "Campus-admin-2026")
        page.goto(args.base + "/admin")
        expect(page.get_by_role("heading", name="管理工作台")).to_be_visible()
        page.screenshot(path=str(args.output / "desktop-admin.png"), full_page=True)
        page.goto(args.base + "/admin/logs")
        page.screenshot(path=str(args.output / "desktop-logs.png"), full_page=True)
        checks.append({"admin": "统计、商品管理、日志页面", "passed": True})
        browser.close()
    assert not errors, errors
    result = {"checks": checks, "javascript_errors": errors, "passed": True}
    (args.output / "browser-results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2)
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
