#!/usr/bin/env python3
"""Create labeled PNG contact sheets without Python imaging packages.

Output: library/overview/<family>.png
Usage: python3 make_overview.py
"""

from __future__ import annotations

import html
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from compose_figure import inline_icon

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CATALOG_PATH = ROOT / "library" / "catalog.json"
OUTPUT = ROOT / "library" / "overview"


def family_of(entry: dict) -> str:
    path = entry.get("svg", "")
    parts = path.split("/")
    folder = parts[1] if len(parts) > 1 else "misc"
    return "originals" if folder == "svg" else folder


def wrap_id(icon_id: str, maximum: int = 19) -> list[str]:
    if len(icon_id) <= maximum:
        return [icon_id]
    split = icon_id.rfind("-", 0, maximum + 1)
    if split >= 6:
        return [icon_id[:split], icon_id[split + 1 : split + 1 + maximum]]
    return [icon_id[: maximum - 1] + "…"]


def make_sheet(family: str, entries: list[dict], catalog: dict[str, dict]) -> str:
    columns = 12
    cell_w, cell_h = 122, 112
    icon_size = 56
    title_h = 42
    padding = 12
    rows = math.ceil(len(entries) / columns)
    width = padding * 2 + columns * cell_w
    height = padding * 2 + title_h + rows * cell_h
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" font-family="Arial, Helvetica, sans-serif">',
        f'<rect width="{width}" height="{height}" fill="#FFFFFF"/>',
        f'<rect width="{width}" height="{title_h}" fill="#2563EB"/>',
        f'<text x="{width/2:.1f}" y="28" text-anchor="middle" fill="#FFFFFF" '
        f'font-size="19" font-weight="700">{html.escape(family)} · {len(entries)} icons</text>',
    ]
    for index, entry in enumerate(entries):
        row, col = divmod(index, columns)
        x = padding + col * cell_w
        y = padding + title_h + row * cell_h
        parts.append(
            f'<rect x="{x+2}" y="{y+2}" width="{cell_w-4}" height="{cell_h-4}" '
            f'rx="7" fill="#FFFFFF" stroke="#E2E8F0"/>'
        )
        try:
            parts.append(
                inline_icon(
                    entry["id"],
                    catalog,
                    x + (cell_w - icon_size) / 2,
                    y + 10,
                    icon_size,
                    "#172033",
                    f"overview-{family}-{index}",
                )
            )
        except (OSError, ValueError):
            parts.append(
                f'<rect x="{x+33}" y="{y+12}" width="56" height="56" fill="#F8FAFC" '
                f'stroke="#CBD5E1" stroke-dasharray="4 3"/>'
            )
        lines = wrap_id(entry["id"])
        for line_index, line in enumerate(lines):
            parts.append(
                f'<text x="{x+cell_w/2:.1f}" y="{y+80+line_index*14}" text-anchor="middle" '
                f'fill="#334155" font-size="10.5">{html.escape(line)}</text>'
            )
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    converter = shutil.which("rsvg-convert")
    if not converter:
        sys.exit("rsvg-convert not found; install librsvg to produce PNG contact sheets")
    try:
        entries = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))["icons"]
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        sys.exit(f"cannot read catalog: {exc}")
    catalog = {entry["id"]: entry for entry in entries}
    groups: dict[str, list[dict]] = {}
    for entry in entries:
        groups.setdefault(family_of(entry), []).append(entry)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    preferred = ["originals", "brand", "lucide", "tabler", "phosphor", "duotone", "fetched"]
    order = preferred + sorted(set(groups) - set(preferred))
    total = 0
    for family in order:
        if family not in groups:
            continue
        family_entries = sorted(groups[family], key=lambda entry: entry["id"])
        png_path = OUTPUT / f"{family}.png"
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".svg", prefix="paper-icons-", delete=False
        ) as handle:
            handle.write(make_sheet(family, family_entries, catalog))
            svg_path = Path(handle.name)
        try:
            subprocess.run(
                [converter, "-f", "png", "-o", str(png_path), str(svg_path)],
                check=True,
            )
        finally:
            svg_path.unlink(missing_ok=True)
        print(f"{family:<10} {len(family_entries):>4} icons -> {png_path}")
        total += len(family_entries)
    print(f"Done: {total} icons across {len(groups)} contact sheets")


if __name__ == "__main__":
    main()
