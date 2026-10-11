#!/usr/bin/env python3
"""把 library/png 里的单色 PNG 用 potrace 矢量化成单色 SVG。

对每张图标取 alpha 通道作为形状掩码(opaque=形状,transparent=背景),
喂给 potrace 生成单填充 SVG。多色图标也会被转成"单色剪影"
(只保留外轮廓,丢失内部彩色细节),作为可一键改色的兜底版本。

用法:
    python3 build_svg_library.py            # 全量重建
    python3 build_svg_library.py target.png # 只处理指定文件
"""
import os
import re
import sys
import subprocess
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "library")
PNG_DIR = os.path.join(LIB, "png")
SVG_DIR = os.path.join(LIB, "svg")

# 这些图标是多色/渐变,矢量化后只剩剪影,在 catalog 里标记 silhouette=true
MULTICOLOR = {"business.png", "ice.png", "puzzle.png", "sprout.png", "workflow.png"}


def trace_one(png_path, svg_path):
    im = Image.open(png_path).convert("RGBA")
    alpha = im.split()[3]
    # opaque 像素 -> 黑(0, potrace 要追踪的形状); 透明 -> 白(255)
    bw = alpha.point(lambda a: 0 if a > 16 else 255).convert("1")
    tmp = svg_path + ".bmp"
    bw.save(tmp, format="BMP")  # potrace 支持 1-bit BMP
    subprocess.run(["potrace", tmp, "-s", "-o", svg_path], check=True,
                   capture_output=True)
    os.remove(tmp)

    # 把 potrace 的 SVG 头规范化成 512 viewBox,方便和 PNG 对齐、内联进图
    w, h = im.size
    text = open(svg_path, encoding="utf-8").read()
    # 丢弃 potrace 自带的 <svg ...> 开头(到第一个 <g 或 <path 之前)
    body_match = re.search(r"(<(?:g|path)[\s\S]*</svg>)", text)
    body = body_match.group(1).replace("</svg>", "").strip() if body_match else text
    # 统一 fill 为纯黑 token,recolor 时再整体替换
    body = re.sub(r'fill="#[0-9A-Fa-f]{3,6}"', 'fill="#000000"', body)
    new_svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {w} {h}" width="{w}" height="{h}">\n'
        f'{body}\n'
        f'</svg>\n'
    )
    open(svg_path, "w", encoding="utf-8").write(new_svg)
    return w, h


def main():
    targets = sys.argv[1:] or sorted(f for f in os.listdir(PNG_DIR) if f.endswith(".png"))
    ok, skip, fail = 0, 0, 0
    for name in targets:
        png = os.path.join(PNG_DIR, name)
        if not os.path.exists(png):
            print(f"  [skip] {name}: 源文件不存在"); skip += 1; continue
        svg = os.path.join(SVG_DIR, os.path.splitext(name)[0] + ".svg")
        try:
            w, h = trace_one(png, svg)
            kind = "silhouette(多色->单色剪影)" if name in MULTICOLOR else "mono"
            print(f"  [ok]   {name:<20} -> {os.path.basename(svg)}  ({w}x{h}, {kind})")
            ok += 1
        except Exception as e:
            print(f"  [fail] {name}: {e}"); fail += 1
    print(f"\n完成: 成功 {ok}, 跳过 {skip}, 失败 {fail}")


if __name__ == "__main__":
    main()
