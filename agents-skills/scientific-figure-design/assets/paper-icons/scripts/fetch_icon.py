#!/usr/bin/env python3
"""Fetch a single SVG icon by name from Lucide and save it under library/fetched/.
Optional --color recolors it on the way in.

Usage:
    python3 fetch_icon.py gpu
    python3 fetch_icon.py cpu --color 2E5C8A
"""
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "library")
FETCH_DIR = os.path.join(LIB, "fetched")
OUT_DIR = os.path.join(LIB, "output")
URL = "https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/{}.svg"


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__); return
    name = args[0].replace(" ", "-").lower()
    color = next((args[i + 1] for i, a in enumerate(args)
                  if a == "--color" and i + 1 < len(args)), None)

    os.makedirs(FETCH_DIR, exist_ok=True)
    try:
        req = urllib.request.Request(URL.format(name),
                                     headers={"User-Agent": "paper-icons-skill"})
        svg = urllib.request.urlopen(req, timeout=15).read().decode("utf-8")
    except Exception as e:
        sys.exit(f"fetch failed for {name!r}: {e}\n"
                 f"check the exact name at https://lucide.dev/icons")

    dst = os.path.join(FETCH_DIR, f"{name}.svg")
    open(dst, "w", encoding="utf-8").write(svg)
    print(f"[ok] {name}: {os.path.abspath(dst)}")

    # Keep semantic search and composition in sync with the new asset.
    subprocess.run([sys.executable, os.path.join(HERE, "build_catalog.py")], check=True)
    print(f"[ok] catalog id: fetched-{name}")

    if color:
        sys.path.insert(0, HERE)
        from recolor import recolor_svg, parse_color  # type: ignore
        hexc = parse_color(color)
        os.makedirs(OUT_DIR, exist_ok=True)
        out = os.path.join(OUT_DIR, f"{name}_{hexc}.svg")
        recolor_svg(dst, hexc, out)
        print(f"[ok] recolored: {os.path.abspath(out)}")


if __name__ == "__main__":
    main()
