#!/usr/bin/env python3
import os
import shutil

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "svg-pixso", "tests")
os.makedirs(OUT, exist_ok=True)

TESTS = {
    "01-rect.svg": '''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
<rect x="0" y="0" width="800" height="600" fill="#F4F6FB"/>
<rect x="80" y="80" width="640" height="440" rx="20" fill="#2563EB"/>
</svg>
''',
    "02-rect-text-en.svg": '''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
<rect x="0" y="0" width="800" height="600" fill="#F4F6FB"/>
<rect x="80" y="80" width="640" height="440" rx="20" fill="#FFFFFF" stroke="#E5E7EB"/>
<text x="120" y="200" font-family="Arial" font-size="36" fill="#111827">Hello Pixso</text>
</svg>
''',
    "03-rect-text-zh.svg": '''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
<rect x="0" y="0" width="800" height="600" fill="#F4F6FB"/>
<rect x="80" y="80" width="640" height="440" rx="20" fill="#FFFFFF" stroke="#E5E7EB"/>
<text x="120" y="200" font-family="PingFang SC" font-size="36" fill="#111827">中文测试</text>
</svg>
''',
    "04-gradient.svg": '''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
<defs>
<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#DBEAFE"/><stop offset="1" stop-color="#2563EB"/>
</linearGradient>
</defs>
<rect x="0" y="0" width="800" height="600" fill="#F4F6FB"/>
<rect x="80" y="80" width="640" height="440" rx="20" fill="url(#g)"/>
</svg>
''',
    "05-path.svg": '''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
<rect x="0" y="0" width="800" height="600" fill="#F4F6FB"/>
<rect x="80" y="80" width="640" height="440" rx="20" fill="#FFFFFF" stroke="#E5E7EB"/>
<path d="M21 21l-4.35-4.35M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15z" transform="translate(300,220) scale(6)" fill="none" stroke="#2563EB" stroke-width="2"/>
</svg>
''',
}

for name, svg in TESTS.items():
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)

src_png = os.path.abspath(os.path.join(BASE, "..", "UI界面", "12-移动端商品详情.png"))
if os.path.exists(src_png):
    shutil.copyfile(src_png, os.path.join(OUT, "06-png.png"))

print("generated", OUT)
