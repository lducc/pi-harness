#!/usr/bin/env python3
"""Recolor an icon from the library and output PNG + SVG.

Resolution order for the icon id: catalog.json (covers all 549 icons) →
library/svg/ → library/fetched/ (backward compatible).

PNG: replace the RGB of every opaque pixel (alpha kept). For icons that ship only
     as SVG (lucide/tabler/phosphor/duotone/brand), the recolored SVG is rasterized
     to PNG via rsvg-convert (transparent background) if available.
SVG: replace every fill / stroke attribute (incl. currentColor).

Usage:
    python3 recolor.py database --color 2E5C8A
    python3 recolor.py lucide-brain --color navy
    python3 recolor.py target --color "#C0392B" --format svg --size 256
"""
import os
import re
import sys
import json
import shutil
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "library")
PNG_DIR = os.path.join(LIB, "png")
SVG_DIR = os.path.join(LIB, "svg")
OUT_DIR = os.path.join(LIB, "output")
CATALOG = os.path.join(LIB, "catalog.json")

# Paper-friendly color aliases (extend as you like)
NAMED = {
    "black": "#1A1A1A", "navy": "#2E5C8A", "blue": "#2E5C8A",
    "crimson": "#C0392B", "red": "#C0392B", "green": "#2E8B57",
    "teal": "#2A9D8F", "orange": "#E07B00", "purple": "#6A4C93",
    "gray": "#6B7280", "grey": "#6B7280",
}


def parse_color(s):
    if not s:
        return None
    s = s.strip().lstrip("#")
    if s.lower() in NAMED:
        s = NAMED[s.lower()].lstrip("#")
    if re.fullmatch(r"[0-9A-Fa-f]{3}", s):
        s = "".join(c * 2 for c in s)
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", s):
        sys.exit(f"invalid color: {s!r}. Use hex (e.g. 2E5C8A / #C0392B) or alias {list(NAMED)}")
    return s.upper()


def _load_catalog():
    try:
        return {i["id"]: i for i in json.load(open(CATALOG, encoding="utf-8"))["icons"]}
    except Exception:
        return {}


def resolve(icon):
    """Return (svg_path_or_None, png_path_or_None) for an icon id."""
    cat = _load_catalog()
    root = os.path.join(HERE, "..")           # paper-icons/
    entry = cat.get(icon)
    if entry:
        svg = os.path.join(root, entry["svg"]) if entry.get("svg") else None
        png = os.path.join(root, entry["png"]) if entry.get("png") else None
        svg = svg if (svg and os.path.exists(svg)) else None
        png = png if (png and os.path.exists(png)) else None
        if svg or png:
            return svg, png
    # backward-compatible fallbacks for non-catalog ids
    svg = os.path.join(SVG_DIR, icon + ".svg")
    svg = svg if os.path.exists(svg) else None
    if not svg:
        f = os.path.join(LIB, "fetched", icon + ".svg")
        svg = f if os.path.exists(f) else None
    png = os.path.join(PNG_DIR, icon + ".png")
    png = png if os.path.exists(png) else None
    return svg, png


def recolor_png(src_png, target_hex, dst_png):
    """Recolor a PNG when no SVG source exists. Pillow is optional."""
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        raise RuntimeError(
            "this icon has no SVG source; PNG recoloring requires Pillow and NumPy"
        )
    im = Image.open(src_png).convert("RGBA")
    r, g, b = int(target_hex[0:2], 16), int(target_hex[2:4], 16), int(target_hex[4:6], 16)
    arr = np.array(im)
    opaque = arr[:, :, 3] > 0
    arr[opaque, 0] = r
    arr[opaque, 1] = g
    arr[opaque, 2] = b
    Image.fromarray(arr, mode="RGBA").save(dst_png)
    return dst_png


def recolor_svg(src_svg, target_hex, dst_svg):
    text = open(src_svg, encoding="utf-8").read()
    hexc = target_hex
    text = re.sub(r'fill="#?[0-9A-Fa-f]{3,6}"', f'fill="#{hexc}"', text)
    text = re.sub(r'stroke="#?[0-9A-Fa-f]{3,6}"', f'stroke="#{hexc}"', text)
    text = re.sub(r'fill:\s*#?[0-9A-Fa-f]{3,6}', f'fill:#{hexc}', text)
    text = re.sub(r'stroke:\s*#?[0-9A-Fa-f]{3,6}', f'stroke:#{hexc}', text)
    text = text.replace('="currentColor"', f'="#{hexc}"')
    text = text.replace(':currentColor', f':#{hexc}')
    open(dst_svg, "w", encoding="utf-8").write(text)
    return dst_svg


def rasterize_svg(src_svg, dst_png, size=512):
    """SVG → PNG (transparent bg) via rsvg-convert. Returns True on success."""
    if not shutil.which("rsvg-convert"):
        return False
    subprocess.run(
        ["rsvg-convert", "-w", str(size), "-h", str(size), src_svg, "-o", dst_png],
        check=True, capture_output=True)
    return True


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__); return
    icon = args[0]
    color = None
    fmt = "both"
    out = OUT_DIR
    size = 512
    i = 1
    while i < len(args):
        a = args[i]
        if a == "--color" and i + 1 < len(args): color = args[i + 1]; i += 2
        elif a == "--format" and i + 1 < len(args): fmt = args[i + 1]; i += 2
        elif a == "--out" and i + 1 < len(args): out = args[i + 1]; i += 2
        elif a == "--size" and i + 1 < len(args): size = int(args[i + 1]); i += 2
        else: i += 1
    target = parse_color(color)
    if not target:
        sys.exit("missing --color. e.g. --color 2E5C8A")
    if fmt not in ("both", "png", "svg"):
        sys.exit("--format must be one of: both, png, svg")

    svg_src, png_src = resolve(icon)
    if not svg_src and not png_src:
        sys.exit(f"icon {icon!r} not found. Check library/catalog.json for the id.")
    entry = _load_catalog().get(icon)
    if entry and not entry.get("recolorable", False):
        sys.exit(
            f"icon {icon!r} is marked non-recolorable ({entry.get('color_type', 'color')}); "
            "preserve its official/source colors"
        )
    os.makedirs(out, exist_ok=True)
    results = []

    # Build one recolored SVG for vector output and/or deterministic rasterization.
    recolored_svg = None
    temporary_svg = False
    if svg_src:
        if fmt in ("both", "svg"):
            recolored_svg = os.path.join(out, f"{icon}_{target}.svg")
        else:
            handle = tempfile.NamedTemporaryFile(prefix="paper-icon-", suffix=".svg", delete=False)
            recolored_svg = handle.name
            handle.close()
            temporary_svg = True
        recolor_svg(svg_src, target, recolored_svg)
        if not temporary_svg:
            results.append(recolored_svg)

    # PNG output
    if fmt in ("both", "png"):
        dst_png = os.path.join(out, f"{icon}_{target}.png")
        if recolored_svg:
            if rasterize_svg(recolored_svg, dst_png, size):
                results.append(dst_png)
            else:
                print("[warn] rsvg-convert not installed; PNG output skipped. "
                      "Install librsvg or request SVG only.", file=sys.stderr)
        elif png_src:
            try:
                recolor_png(png_src, target, dst_png)
                results.append(dst_png)
            except RuntimeError as exc:
                sys.exit(str(exc))

    if temporary_svg and recolored_svg:
        try:
            os.unlink(recolored_svg)
        except OSError:
            pass

    if not results:
        sys.exit(f"could not produce any output for {icon!r}")
    print("Generated:")
    for r in results:
        print("  " + os.path.abspath(r))


if __name__ == "__main__":
    main()
