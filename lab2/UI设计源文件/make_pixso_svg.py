#!/usr/bin/env python3
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "svg")
DST = os.path.join(BASE, "svg-pixso")
os.makedirs(DST, exist_ok=True)

FILTER_BLOCK = re.compile(r'<filter id="shadow".*?</filter>\s*', re.S)
FILTER_ATTR = re.compile(r'\s+filter="url\(#shadow\)"')

SIMPLE = '''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
<rect x="0" y="0" width="800" height="600" fill="#F4F6FB"/>
<rect x="40" y="40" width="720" height="520" rx="16" fill="#FFFFFF" stroke="#E5E7EB"/>
<text x="80" y="110" font-family="PingFang SC, Hiragino Sans GB, Arial, sans-serif" font-size="28" font-weight="700" fill="#111827">Pixso SVG 测试</text>
<text x="80" y="150" font-family="PingFang SC, Hiragino Sans GB, Arial, sans-serif" font-size="14" fill="#6B7280">如果能正常导入，说明无滤镜 SVG 兼容。</text>
<rect x="80" y="190" width="180" height="44" rx="8" fill="#2563EB"/>
<text x="170" y="218" text-anchor="middle" font-family="PingFang SC, Hiragino Sans GB, Arial, sans-serif" font-size="14" font-weight="600" fill="#FFFFFF">测试按钮</text>
</svg>
'''


def clean_svg(text):
    text = FILTER_BLOCK.sub("", text)
    text = FILTER_ATTR.sub("", text)
    return text


def main():
    count = 0
    for name in sorted(os.listdir(SRC)):
        if not name.endswith(".svg"):
            continue
        src = os.path.join(SRC, name)
        dst = os.path.join(DST, name)
        with open(src, encoding="utf-8") as f:
            svg = clean_svg(f.read())
        with open(dst, "w", encoding="utf-8") as f:
            f.write(svg)
        count += 1

    with open(os.path.join(DST, "test-mobile-detail.svg"), "w", encoding="utf-8") as f:
        with open(os.path.join(SRC, "12-移动端商品详情.svg"), encoding="utf-8") as src:
            f.write(clean_svg(src.read()))

    with open(os.path.join(DST, "test-simple.svg"), "w", encoding="utf-8") as f:
        f.write(SIMPLE)

    print(f"generated {count} Pixso-compatible SVGs in {DST}")
    print("test files: test-mobile-detail.svg, test-simple.svg")


if __name__ == "__main__":
    main()
