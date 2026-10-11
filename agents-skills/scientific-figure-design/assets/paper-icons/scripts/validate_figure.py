#!/usr/bin/env python3
"""Validate structural and publication-readiness properties of an SVG figure.

This is a deterministic quality gate, not a substitute for visual inspection.

Usage:
  python3 validate_figure.py figure.svg
  python3 validate_figure.py figure.svg --strict
"""

from __future__ import annotations

import argparse
import html
import re
import unicodedata
from collections import Counter
from pathlib import Path


ATTR_RE = re.compile(
    r"""([:\w.-]+)\s*=\s*(?:"([^"]*)"|'([^']*)')""",
    re.DOTALL,
)


def attrs(markup: str) -> dict[str, str]:
    return {
        match.group(1).lower(): html.unescape(match.group(2) if match.group(2) is not None else match.group(3))
        for match in ATTR_RE.finditer(markup)
    }


def plain_text(markup: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", markup)).split())


def parse_number(value: str | None) -> float | None:
    if value is None:
        return None
    match = re.match(r"\s*(-?\d+(?:\.\d+)?)", value)
    return float(match.group(1)) if match else None


def text_units(text: str) -> float:
    units = 0.0
    for char in text:
        if char.isspace():
            units += 0.35
        elif unicodedata.east_asian_width(char) in ("W", "F", "A"):
            units += 1.0
        elif char in "ilI.,:;|'":
            units += 0.32
        elif char in "MW@#%":
            units += 0.9
        else:
            units += 0.58
    return units


def relative_luminance(color: str) -> float:
    raw = color.lstrip("#")
    if len(raw) == 3:
        raw = "".join(char * 2 for char in raw)
    channels = [int(raw[index : index + 2], 16) / 255 for index in (0, 2, 4)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a: str, b: str) -> float:
    la, lb = relative_luminance(a), relative_luminance(b)
    light, dark = max(la, lb), min(la, lb)
    return (light + 0.05) / (dark + 0.05)


def validate(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        root_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read SVG: {exc}"], []
    root_match = re.search(r"<svg\b([^>]*)>", root_text, re.IGNORECASE | re.DOTALL)
    if not root_match:
        return ["root <svg> element is missing"], []
    if not re.search(r"</svg>\s*$", root_text, re.IGNORECASE):
        errors.append("closing </svg> element is missing")
    root_attrs = attrs(root_match.group(1))
    viewbox = root_attrs.get("viewbox")
    if not viewbox:
        errors.append("root SVG has no viewBox")
        width = height = None
    else:
        try:
            _, _, width, height = (float(value) for value in viewbox.replace(",", " ").split())
            if width <= 0 or height <= 0:
                errors.append("viewBox width and height must be positive")
        except ValueError:
            errors.append(f"invalid viewBox: {viewbox!r}")
            width = height = None
    physical_width_mm = None
    if root_attrs.get("width", "").strip().lower().endswith("mm"):
        physical_width_mm = parse_number(root_attrs["width"])

    title = re.search(r"<title\b[^>]*>(.*?)</title>", root_text, re.IGNORECASE | re.DOTALL)
    description = re.search(r"<desc\b[^>]*>(.*?)</desc>", root_text, re.IGNORECASE | re.DOTALL)
    if not title or not plain_text(title.group(1)):
        warnings.append("missing non-empty top-level <title> metadata")
    if not description or not plain_text(description.group(1)):
        warnings.append("missing non-empty top-level <desc> metadata")

    tags = []
    for match in re.finditer(r"<([A-Za-z][\w:-]*)\b([^>]*)>", root_text, re.DOTALL):
        if match.group(0).startswith(("<!--", "<?", "<!")):
            continue
        raw_attributes = match.group(2)
        names = [item.group(1).lower() for item in ATTR_RE.finditer(raw_attributes)]
        duplicate_attributes = [
            key for key, count in Counter(names).items() if count > 1
        ]
        if duplicate_attributes:
            errors.append(
                f"<{match.group(1)}> has duplicate attributes: "
                + ", ".join(duplicate_attributes)
            )
        tags.append((match.group(1).lower(), attrs(raw_attributes)))
    ids = [attributes["id"] for _, attributes in tags if attributes.get("id")]
    duplicates = [key for key, count in Counter(ids).items() if count > 1]
    if duplicates:
        errors.append("duplicate SVG ids: " + ", ".join(duplicates[:8]))

    external = re.findall(r'(?:href|xlink:href)\s*=\s*["\']((?!#|data:)[^"\']+)', root_text)
    if external:
        warnings.append("external asset references reduce portability: " + ", ".join(external[:4]))
    raster_images = [
        attributes
        for tag, attributes in tags
        if tag == "image"
        and re.search(r"\.(?:png|jpe?g|gif|webp)(?:[?#]|$)", attributes.get("href", ""), re.IGNORECASE)
    ]
    if raster_images:
        warnings.append(f"{len(raster_images)} raster image(s) embedded or referenced in a vector figure")

    colors = re.findall(r"#[0-9A-Fa-f]{6}\b", root_text)
    unique_colors = sorted(set(color.upper() for color in colors))
    non_neutral = [
        color
        for color in unique_colors
        if max(hex_to_int(color)) - min(hex_to_int(color)) > 18
    ]
    if len(non_neutral) > 8:
        warnings.append(f"figure uses {len(non_neutral)} chromatic colors; check whether color has a stable meaning")

    font_families = {
        attributes["font-family"]
        for _, attributes in tags
        if attributes.get("font-family")
    }
    root_font = root_attrs.get("font-family")
    if root_font:
        font_families.add(root_font)
    if not font_families:
        warnings.append("no explicit font-family; rendering may vary across systems")
    elif len(font_families) > 2:
        warnings.append(f"more than two font-family declarations: {sorted(font_families)}")

    canvas_match = re.search(r"<rect\b([^>]*)>", root_text[root_match.end() :], re.IGNORECASE | re.DOTALL)
    canvas_attrs = attrs(canvas_match.group(1)) if canvas_match else {}
    background = canvas_attrs.get("fill", "#FFFFFF")

    for text_match in re.finditer(r"<text\b([^>]*)>(.*?)</text>", root_text, re.IGNORECASE | re.DOTALL):
        text_attrs = attrs(text_match.group(1))
        inner = text_match.group(2)
        content = plain_text(inner)
        size = parse_number(text_attrs.get("font-size"))
        if size is not None and physical_width_mm and width:
            final_points = size * physical_width_mm / width / 25.4 * 72
            if final_points < 7:
                warnings.append(
                    f"text below 7 pt at final width: {content[:50]!r} ({final_points:.1f} pt)"
                )
        elif size is not None and size < 10:
            warnings.append(f"small text without physical-width metadata: {content[:50]!r} ({size:g})")
        x = parse_number(text_attrs.get("x"))
        y = parse_number(text_attrs.get("y"))
        if width and height and x is not None and y is not None:
            if x < -0.5 or x > width + 0.5 or y < -0.5 or y > height + 0.5:
                errors.append(f"text anchor outside viewBox: {content[:50]!r} at ({x:g}, {y:g})")
        max_width = parse_number(text_attrs.get("data-max-width"))
        if max_width and size:
            for line in re.finditer(r"<tspan\b[^>]*>(.*?)</tspan>", inner, re.IGNORECASE | re.DOTALL):
                line_text = plain_text(line.group(1))
                estimated = text_units(line_text) * size
                if estimated > max_width * 1.05:
                    warnings.append(
                        f"possible text overflow: {line_text!r} estimated {estimated:.0f} > {max_width:.0f}"
                    )

        fill = text_attrs.get("fill")
        if (
            fill
            and "badge-label" not in text_attrs.get("class", "").split()
            and re.fullmatch(r"#[0-9A-Fa-f]{6}", fill)
        ):
            if background and re.fullmatch(r"#[0-9A-Fa-f]{6}", background):
                ratio = contrast(fill, background)
                if size and size <= 18 and ratio < 3.2:
                    warnings.append(f"low text contrast ({ratio:.1f}:1): {content[:50]!r}")

    edge_count = sum(1 for _, attributes in tags if "edge" in attributes.get("class", "").split())
    node_count = sum(1 for _, attributes in tags if "node" in attributes.get("class", "").split())
    if edge_count > max(12, node_count * 2):
        warnings.append(f"dense topology: {edge_count} edges for {node_count} nodes; inspect crossings")

    marker_refs = set(re.findall(r"url\(#([^)]+)\)", root_text))
    missing_markers = marker_refs - set(ids)
    if missing_markers:
        errors.append("references to missing SVG ids: " + ", ".join(sorted(missing_markers)[:8]))
    return errors, list(dict.fromkeys(warnings))


def hex_to_int(color: str) -> tuple[int, int, int]:
    raw = color.lstrip("#")
    return tuple(int(raw[index : index + 2], 16) for index in (0, 2, 4))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", type=Path)
    parser.add_argument("--strict", action="store_true", help="Treat warnings as a failing exit status")
    args = parser.parse_args()
    errors, warnings = validate(args.svg)
    for message in errors:
        print(f"ERROR  {message}")
    for message in warnings:
        print(f"WARN   {message}")
    if not errors and not warnings:
        print(f"PASS   {args.svg} passed structural checks")
    else:
        print(f"SUMMARY  {len(errors)} error(s), {len(warnings)} warning(s)")
    if errors or (args.strict and warnings):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
