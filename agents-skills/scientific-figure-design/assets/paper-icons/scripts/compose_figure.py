#!/usr/bin/env python3
"""Compose a publication-oriented SVG figure from a JSON specification.

The output SVG is self-contained: icons are inlined, labels are wrapped, and
connectors are routed behind nodes. Optional PDF/PNG export uses rsvg-convert.

Usage:
  python3 compose_figure.py spec.json --out figure.svg
  python3 compose_figure.py spec.json --out figure.svg --pdf figure.pdf --png figure.png
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CATALOG = ROOT / "library" / "catalog.json"

DEFAULT_PALETTE = {
    "canvas": "#FFFFFF",
    "ink": "#172033",
    "muted": "#5B6472",
    "stroke": "#CBD5E1",
    "neutral": "#64748B",
    "accent": "#2563EB",
    "secondary": "#7C3AED",
    "success": "#15803D",
    "warning": "#B45309",
    "danger": "#B91C1C",
}
PHYSICAL_WIDTH_MM = {"single": 85.0, "double": 178.0}
DEFAULT_CANVAS = {"single": (560.0, 420.0), "double": (1080.0, 480.0)}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    if len(color) == 3:
        color = "".join(ch * 2 for ch in color)
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def blend(color: str, background: str = "#FFFFFF", amount: float = 0.9) -> str:
    front = hex_to_rgb(color)
    back = hex_to_rgb(background)
    mixed = [round(f * (1 - amount) + b * amount) for f, b in zip(front, back)]
    return "#" + "".join(f"{value:02X}" for value in mixed)


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


def wrap_text(text: str, max_width: float, font_size: float, max_lines: int = 2) -> list[str]:
    if not text:
        return []
    capacity = max(max_width / max(font_size, 1), 1)
    words = text.split()
    if len(words) == 1 and text_units(text) > capacity:
        words = list(text)
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if text_units(candidate) <= capacity or not current:
            current = candidate
            continue
        lines.append(current)
        current = word
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and text_units(last + "…") > capacity:
            last = last[:-1]
        lines[-1] = last.rstrip() + "…"
    return lines


def read_catalog() -> dict[str, dict]:
    try:
        return {
            entry["id"]: entry
            for entry in json.loads(CATALOG.read_text(encoding="utf-8"))["icons"]
        }
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        sys.exit(f"cannot read icon catalog {CATALOG}: {exc}")


def recolor_markup(markup: str, target: str) -> str:
    markup = markup.replace("currentColor", target)
    markup = re.sub(
        r'((?:fill|stroke)\s*=\s*["\'])(?!none|white|#fff(?:fff)?)(?:black|#[0-9a-fA-F]{3,8})(["\'])',
        rf"\g<1>{target}\g<2>",
        markup,
        flags=re.IGNORECASE,
    )
    markup = re.sub(
        r"((?:fill|stroke)\s*:\s*)(?!none|white|#fff(?:fff)?)(?:black|#[0-9a-fA-F]{3,8})",
        rf"\g<1>{target}",
        markup,
        flags=re.IGNORECASE,
    )
    return markup


def inline_icon(
    icon_id: str,
    catalog: dict[str, dict],
    x: float,
    y: float,
    size: float,
    color: str,
    instance: str,
) -> str:
    entry = catalog.get(icon_id)
    if not entry:
        raise ValueError(f"unknown icon id {icon_id!r}")
    relative = entry.get("svg")
    if not relative:
        raise ValueError(f"icon {icon_id!r} has no SVG source")
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    match = re.search(r"<svg\b([^>]*)>(.*)</svg>\s*$", text, re.DOTALL | re.IGNORECASE)
    if not match:
        raise ValueError(f"invalid SVG source for {icon_id!r}: {path}")
    attrs, inner = match.groups()
    viewbox = re.search(r'viewBox\s*=\s*["\']([^"\']+)["\']', attrs, re.IGNORECASE)
    vb = viewbox.group(1) if viewbox else "0 0 24 24"
    inherited = []
    for attr_match in re.finditer(r'([:\w.-]+)\s*=\s*(["\'])(.*?)\2', attrs, re.DOTALL):
        name, value = attr_match.group(1), attr_match.group(3)
        if name.lower() in {
            "xmlns",
            "xmlns:xlink",
            "viewbox",
            "width",
            "height",
            "class",
            "aria-hidden",
        }:
            continue
        inherited.append(f'{name}="{esc(value)}"')
    inherited_markup = " ".join(inherited)

    # SVG ids share a global document namespace; prefix them per instance.
    id_map = {
        old: f"icon-{instance}-{old}"
        for old in re.findall(r'\bid\s*=\s*["\']([^"\']+)["\']', inner)
    }
    for old, new in id_map.items():
        inner = re.sub(rf'(\bid\s*=\s*["\']){re.escape(old)}(["\'])', rf"\g<1>{new}\g<2>", inner)
        inner = inner.replace(f"url(#{old})", f"url(#{new})")
        inner = inner.replace(f'href="#{old}"', f'href="#{new}"')
        inner = inner.replace(f"xlink:href=\"#{old}\"", f'xlink:href="#{new}"')

    if entry.get("recolorable"):
        inherited_markup = recolor_markup(inherited_markup, color)
        inner = recolor_markup(inner, color)
    return (
        f'<svg class="node-icon" x="{x:.1f}" y="{y:.1f}" width="{size:.1f}" height="{size:.1f}" '
        f'viewBox="{esc(vb)}" preserveAspectRatio="xMidYMid meet" aria-hidden="true" '
        f'{inherited_markup}>{inner}</svg>'
    )


def validate_spec(spec: dict, catalog: dict[str, dict]) -> None:
    errors = []
    metadata = spec.get("metadata", {})
    if not metadata.get("title"):
        errors.append("metadata.title is required")
    if not metadata.get("description"):
        errors.append("metadata.description is required")
    nodes = spec.get("nodes", [])
    if not nodes:
        errors.append("at least one node is required")
    ids = [node.get("id") for node in nodes]
    if any(not node_id for node_id in ids):
        errors.append("every node requires id")
    if len(ids) != len(set(ids)):
        errors.append("node ids must be unique")
    for node_id in ids:
        if node_id and not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*", str(node_id)):
            errors.append(
                f"node id {node_id!r} must start with a letter and contain only letters, digits, _, ., or -"
            )
    node_ids = set(ids)
    for node in nodes:
        if not node.get("label"):
            errors.append(f"node {node.get('id')!r} requires label")
        if node.get("icon") and node["icon"] not in catalog:
            errors.append(f"node {node.get('id')!r} references unknown icon {node['icon']!r}")
    for index, edge in enumerate(spec.get("edges", [])):
        if edge.get("from") not in node_ids or edge.get("to") not in node_ids:
            errors.append(f"edge {index} references an unknown node")
    group_ids = [group.get("id") for group in spec.get("groups", [])]
    if len(group_ids) != len(set(group_ids)):
        errors.append("group ids must be unique")
    for group_id in group_ids:
        if group_id and not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*", str(group_id)):
            errors.append(
                f"group id {group_id!r} must start with a letter and contain only letters, digits, _, ., or -"
            )
    for node in nodes:
        if node.get("group") and node["group"] not in group_ids:
            errors.append(f"node {node['id']!r} references unknown group {node['group']!r}")
    if errors:
        sys.exit("invalid figure spec:\n- " + "\n- ".join(errors))


def geometry(spec: dict) -> tuple[dict[str, dict], float, float, float, str]:
    figure = spec.get("figure", {})
    column = figure.get("column", "double")
    if column not in DEFAULT_CANVAS:
        raise ValueError("figure.column must be 'single' or 'double'")
    default_w, default_h = DEFAULT_CANVAS[column]
    width = float(figure.get("width", default_w))
    height = float(figure.get("height", default_h))
    physical = float(figure.get("physical_width_mm", PHYSICAL_WIDTH_MM[column]))
    layout = figure.get("layout", "pipeline")
    nodes = [dict(node) for node in spec["nodes"]]

    heading_space = 42 if figure.get("heading") else 0
    top = 48 + heading_space
    bottom = 40
    left = 48
    right = 48
    available_w = width - left - right
    available_h = height - top - bottom

    if layout == "pipeline":
        direction = figure.get("direction", "horizontal")
        gap = float(figure.get("gap", 42))
        if direction == "horizontal":
            node_w = min(225.0, (available_w - gap * (len(nodes) - 1)) / len(nodes))
            if node_w < 125:
                raise ValueError("pipeline nodes are too narrow; use grid, vertical, or a wider canvas")
            node_h = float(figure.get("node_height", 130))
            total_w = node_w * len(nodes) + gap * (len(nodes) - 1)
            start_x = left + (available_w - total_w) / 2
            y = top + (available_h - node_h) / 2
            for index, node in enumerate(nodes):
                node.setdefault("x", start_x + index * (node_w + gap))
                node.setdefault("y", y)
                node.setdefault("w", node_w)
                node.setdefault("h", node_h)
        elif direction == "vertical":
            node_h = min(112.0, (available_h - gap * (len(nodes) - 1)) / len(nodes))
            if node_h < 80:
                raise ValueError("vertical pipeline nodes are too short; increase height or use grid")
            node_w = min(float(figure.get("node_width", 300)), available_w)
            x = left + (available_w - node_w) / 2
            total_h = node_h * len(nodes) + gap * (len(nodes) - 1)
            start_y = top + (available_h - total_h) / 2
            for index, node in enumerate(nodes):
                node.setdefault("x", x)
                node.setdefault("y", start_y + index * (node_h + gap))
                node.setdefault("w", node_w)
                node.setdefault("h", node_h)
        else:
            raise ValueError("figure.direction must be horizontal or vertical")
    elif layout == "grid":
        columns = int(figure.get("columns", 2))
        if columns < 1:
            raise ValueError("figure.columns must be positive")
        rows = math.ceil(len(nodes) / columns)
        gap_x = float(figure.get("gap_x", 28))
        gap_y = float(figure.get("gap_y", 28))
        node_w = (available_w - gap_x * (columns - 1)) / columns
        node_h = (available_h - gap_y * (rows - 1)) / rows
        for index, node in enumerate(nodes):
            row, col = divmod(index, columns)
            node.setdefault("x", left + col * (node_w + gap_x))
            node.setdefault("y", top + row * (node_h + gap_y))
            node.setdefault("w", node_w)
            node.setdefault("h", node_h)
    elif layout == "freeform":
        for node in nodes:
            missing = [key for key in ("x", "y", "w", "h") if key not in node]
            if missing:
                raise ValueError(f"freeform node {node['id']!r} is missing {', '.join(missing)}")
    else:
        raise ValueError("figure.layout must be pipeline, grid, or freeform")
    for node in nodes:
        x, y, node_w, node_h = (float(node[key]) for key in ("x", "y", "w", "h"))
        if node_w <= 0 or node_h <= 0:
            raise ValueError(f"node {node['id']!r} must have positive width and height")
        if x < 0 or y < 0 or x + node_w > width or y + node_h > height:
            raise ValueError(f"node {node['id']!r} extends outside the {width:g} x {height:g} viewBox")
    return {node["id"]: node for node in nodes}, width, height, physical, column


def boundary_point(source: dict, target: dict) -> tuple[float, float]:
    sx = source["x"] + source["w"] / 2
    sy = source["y"] + source["h"] / 2
    tx = target["x"] + target["w"] / 2
    ty = target["y"] + target["h"] / 2
    dx, dy = tx - sx, ty - sy
    if dx == 0 and dy == 0:
        return sx, sy
    scale_x = (source["w"] / 2) / abs(dx) if dx else float("inf")
    scale_y = (source["h"] / 2) / abs(dy) if dy else float("inf")
    scale = min(scale_x, scale_y)
    return sx + dx * scale, sy + dy * scale


def edge_path(source: dict, target: dict, route: str) -> tuple[str, float, float]:
    sx, sy = boundary_point(source, target)
    tx, ty = boundary_point(target, source)
    mx, my = (sx + tx) / 2, (sy + ty) / 2
    if source is target:
        x = source["x"] + source["w"]
        y = source["y"] + source["h"] / 2
        return f"M {x:.1f} {y:.1f} C {x+70:.1f} {y-70:.1f}, {x+70:.1f} {y+70:.1f}, {x:.1f} {y+10:.1f}", x + 65, y
    if route == "straight":
        return f"M {sx:.1f} {sy:.1f} L {tx:.1f} {ty:.1f}", mx, my
    if route == "curve":
        offset = max(45.0, min(120.0, abs(tx - sx) * 0.35 + abs(ty - sy) * 0.2))
        if abs(tx - sx) >= abs(ty - sy):
            direction = 1 if tx >= sx else -1
            path = f"M {sx:.1f} {sy:.1f} C {sx+direction*offset:.1f} {sy:.1f}, {tx-direction*offset:.1f} {ty:.1f}, {tx:.1f} {ty:.1f}"
        else:
            direction = 1 if ty >= sy else -1
            path = f"M {sx:.1f} {sy:.1f} C {sx:.1f} {sy+direction*offset:.1f}, {tx:.1f} {ty-direction*offset:.1f}, {tx:.1f} {ty:.1f}"
        return path, mx, my
    if abs(tx - sx) >= abs(ty - sy):
        return f"M {sx:.1f} {sy:.1f} H {mx:.1f} V {ty:.1f} H {tx:.1f}", mx, (sy + ty) / 2
    return f"M {sx:.1f} {sy:.1f} V {my:.1f} H {tx:.1f} V {ty:.1f}", (sx + tx) / 2, my


def shape_markup(node: dict, fill: str, stroke: str) -> str:
    x, y, w, h = (float(node[key]) for key in ("x", "y", "w", "h"))
    shape = node.get("shape", "round")
    common = f'fill="{fill}" stroke="{stroke}" stroke-width="1.6" vector-effect="non-scaling-stroke"'
    if shape == "circle":
        radius = min(w, h) / 2
        return f'<circle cx="{x+w/2:.1f}" cy="{y+h/2:.1f}" r="{radius:.1f}" {common}/>'
    if shape == "database":
        ry = min(13.0, h * 0.12)
        return (
            f'<path d="M{x:.1f},{y+ry:.1f} Q{x:.1f},{y:.1f} {x+w/2:.1f},{y:.1f} '
            f'Q{x+w:.1f},{y:.1f} {x+w:.1f},{y+ry:.1f} V{y+h-ry:.1f} '
            f'Q{x+w:.1f},{y+h:.1f} {x+w/2:.1f},{y+h:.1f} '
            f'Q{x:.1f},{y+h:.1f} {x:.1f},{y+h-ry:.1f} Z" {common}/>'
        )
    rx = 3 if shape == "rect" else (h / 2 if shape == "pill" else 12)
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" {common}/>'


def node_markup(
    node: dict,
    palette: dict[str, str],
    catalog: dict[str, dict],
    index: int,
) -> str:
    x, y, w, h = (float(node[key]) for key in ("x", "y", "w", "h"))
    tone = node.get("tone", "neutral")
    stroke = palette.get(tone, palette["neutral"])
    fill = blend(stroke, palette["canvas"], 0.92 if tone != "neutral" else 0.95)
    pieces = [f'<g class="node" id="node-{esc(node["id"])}">', shape_markup(node, fill, stroke)]

    icon = node.get("icon")
    icon_size = min(40.0, h * 0.31)
    inner_pad = max(14.0, min(20.0, w * 0.08))
    if icon:
        icon_x = x + inner_pad
        icon_y = y + (h - icon_size) / 2
        pieces.append(
            inline_icon(icon, catalog, icon_x, icon_y, icon_size, stroke, f"{index}-{node['id']}")
        )
        text_x = icon_x + icon_size + 13
        text_width = w - (text_x - x) - inner_pad
        anchor = "start"
    else:
        text_x = x + w / 2
        text_width = w - inner_pad * 2
        anchor = "middle"

    label_size = 19.0
    subtitle_size = 16.5
    label_lines = wrap_text(str(node["label"]), text_width, label_size, 2)
    subtitle_lines = wrap_text(str(node.get("subtitle", "")), text_width, subtitle_size, 2)
    line_gap = 22
    subtitle_gap = 19
    total_h = len(label_lines) * line_gap + (5 + len(subtitle_lines) * subtitle_gap if subtitle_lines else 0)
    start_y = y + (h - total_h) / 2 + label_size * 0.8

    pieces.append(
        f'<text class="node-label" x="{text_x:.1f}" y="{start_y:.1f}" '
        f'text-anchor="{anchor}" fill="{palette["ink"]}" font-size="{label_size:.1f}" '
        f'font-weight="600" data-max-width="{text_width:.1f}">'
    )
    for line_index, line in enumerate(label_lines):
        dy = 0 if line_index == 0 else line_gap
        pieces.append(f'<tspan x="{text_x:.1f}" dy="{dy:.1f}">{esc(line)}</tspan>')
    pieces.append("</text>")

    if subtitle_lines:
        subtitle_y = start_y + max(0, len(label_lines) - 1) * line_gap + 23
        pieces.append(
            f'<text class="node-subtitle" x="{text_x:.1f}" y="{subtitle_y:.1f}" '
            f'text-anchor="{anchor}" fill="{palette["muted"]}" font-size="{subtitle_size:.1f}" '
            f'data-max-width="{text_width:.1f}">'
        )
        for line_index, line in enumerate(subtitle_lines):
            dy = 0 if line_index == 0 else subtitle_gap
            pieces.append(f'<tspan x="{text_x:.1f}" dy="{dy:.1f}">{esc(line)}</tspan>')
        pieces.append("</text>")

    if node.get("badge"):
        badge = str(node["badge"])
        badge_w = max(48.0, text_units(badge) * 16.5 + 18)
        badge_x = x + w - badge_w - 9
        badge_y = y - 12.5
        pieces.append(
            f'<rect x="{badge_x:.1f}" y="{badge_y:.1f}" width="{badge_w:.1f}" height="25" '
            f'rx="12.5" fill="{stroke}"/><text class="badge-label" x="{badge_x+badge_w/2:.1f}" y="{badge_y+17.5:.1f}" '
            f'text-anchor="middle" fill="#FFFFFF" font-size="16.5" font-weight="700">{esc(badge)}</text>'
        )
    pieces.append("</g>")
    return "".join(pieces)


def compose(spec: dict) -> tuple[str, float]:
    catalog = read_catalog()
    validate_spec(spec, catalog)
    try:
        nodes, width, height, physical_width, _ = geometry(spec)
    except ValueError as exc:
        sys.exit(str(exc))
    figure = spec.get("figure", {})
    palette = dict(DEFAULT_PALETTE)
    palette.update(figure.get("palette", {}))
    for key, color in palette.items():
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
            sys.exit(f"palette color {key!r} must be six-digit hex, got {color!r}")

    physical_height = physical_width * height / width
    metadata = spec["metadata"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{physical_width:.2f}mm" '
        f'height="{physical_height:.2f}mm" viewBox="0 0 {width:.1f} {height:.1f}" '
        f'font-family="Arial, Helvetica, sans-serif" text-rendering="geometricPrecision" '
        f'role="img" aria-labelledby="figure-title figure-desc">',
        f'<title id="figure-title">{esc(metadata["title"])}</title>',
        f'<desc id="figure-desc">{esc(metadata["description"])}</desc>',
        "<defs>",
        "<style>"
        ".edge{fill:none;stroke-linecap:round;stroke-linejoin:round}"
        ".node-label,.node-subtitle,.edge-label{paint-order:stroke;stroke:none}"
        "</style>",
    ]

    edge_colors = {
        palette.get(edge.get("tone", "neutral"), palette["neutral"])
        for edge in spec.get("edges", [])
    }
    for color in sorted(edge_colors):
        marker_id = "arrow-" + color.lstrip("#").lower()
        parts.append(
            f'<marker id="{marker_id}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker>'
        )
    parts.extend(["</defs>", f'<rect width="{width:.1f}" height="{height:.1f}" fill="{palette["canvas"]}"/>'])

    if figure.get("panel_label"):
        parts.append(
            f'<text x="18" y="30" font-size="20" font-weight="700" fill="{palette["ink"]}">'
            f'{esc(figure["panel_label"])}</text>'
        )
    if figure.get("heading"):
        parts.append(
            f'<text x="{width/2:.1f}" y="46" text-anchor="middle" font-size="20" '
            f'font-weight="700" fill="{palette["ink"]}">{esc(figure["heading"])}</text>'
        )

    # Groups are behind edges and nodes.
    group_map = {group["id"]: group for group in spec.get("groups", [])}
    for group_id, group in group_map.items():
        members = [node for node in nodes.values() if node.get("group") == group_id]
        if not members:
            continue
        pad = float(group.get("padding", 18))
        x = min(float(node["x"]) for node in members) - pad
        y = min(float(node["y"]) for node in members) - pad - 10
        x2 = max(float(node["x"]) + float(node["w"]) for node in members) + pad
        y2 = max(float(node["y"]) + float(node["h"]) for node in members) + pad
        tone = group.get("tone", "neutral")
        color = palette.get(tone, palette["neutral"])
        dash = ' stroke-dasharray="7 5"' if group.get("style", "dashed") == "dashed" else ""
        parts.append(
            f'<g class="group" id="group-{esc(group_id)}">'
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{x2-x:.1f}" height="{y2-y:.1f}" rx="16" '
            f'fill="{blend(color, palette["canvas"], 0.965)}" stroke="{color}" stroke-width="1.3"{dash}/>'
            f'<rect x="{x+12:.1f}" y="{y-12:.1f}" width="{max(110, text_units(str(group.get("label", group_id))) * 16.5 + 22):.1f}" '
            f'height="25" rx="5" fill="{palette["canvas"]}"/>'
            f'<text x="{x+18:.1f}" y="{y+6:.1f}" font-size="16.5" font-weight="600" '
            f'fill="{color}">{esc(group.get("label", group_id))}</text></g>'
        )

    # Edges are behind nodes.
    for index, edge in enumerate(spec.get("edges", [])):
        source = nodes[edge["from"]]
        target = nodes[edge["to"]]
        route = edge.get("route", "orthogonal")
        path, label_x, label_y = edge_path(source, target, route)
        tone = edge.get("tone", "neutral")
        color = palette.get(tone, palette["neutral"])
        marker_id = "arrow-" + color.lstrip("#").lower()
        arrow = edge.get("arrow", "end")
        marker_start = f' marker-start="url(#{marker_id})"' if arrow == "both" else ""
        marker_end = f' marker-end="url(#{marker_id})"' if arrow in ("end", "both") else ""
        dash = ' stroke-dasharray="7 5"' if edge.get("style") == "dashed" else ""
        parts.append(
            f'<path class="edge" id="edge-{index}" d="{path}" stroke="{color}" stroke-width="1.7"'
            f'{dash}{marker_start}{marker_end}/>'
        )
        if edge.get("label"):
            label = str(edge["label"])
            source_cx = source["x"] + source["w"] / 2
            source_cy = source["y"] + source["h"] / 2
            target_cx = target["x"] + target["w"] / 2
            target_cy = target["y"] + target["h"] / 2
            if abs(source_cy - target_cy) < 3:
                label_y = min(source["y"], target["y"]) - 36
            elif abs(source_cx - target_cx) < 3:
                label_x = max(source["x"] + source["w"], target["x"] + target["w"]) + 16
            label_w = max(54.0, text_units(label) * 16.5 + 18)
            parts.append(
                f'<rect x="{label_x-label_w/2:.1f}" y="{label_y-12.5:.1f}" width="{label_w:.1f}" '
                f'height="25" rx="5" fill="{palette["canvas"]}" opacity="0.96"/>'
                f'<text class="edge-label" x="{label_x:.1f}" y="{label_y+5.5:.1f}" '
                f'text-anchor="middle" fill="{palette["muted"]}" font-size="16.5">{esc(label)}</text>'
            )

    for index, node in enumerate(nodes.values()):
        try:
            parts.append(node_markup(node, palette, catalog, index))
        except (OSError, ValueError) as exc:
            sys.exit(str(exc))

    for annotation in spec.get("annotations", []):
        text = str(annotation["text"])
        x, y = float(annotation["x"]), float(annotation["y"])
        tone = annotation.get("tone", "accent")
        color = palette.get(tone, palette["accent"])
        width = max(90.0, text_units(text) * 16.5 + 24)
        parts.append(
            f'<g class="annotation"><rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="28" '
            f'rx="14" fill="{blend(color, palette["canvas"], 0.88)}" stroke="{color}" stroke-width="1"/>'
            f'<text x="{x+width/2:.1f}" y="{y+19.5:.1f}" text-anchor="middle" fill="{color}" '
            f'font-size="16.5" font-weight="600">{esc(text)}</text></g>'
        )
    parts.append("</svg>")
    return "\n".join(parts), physical_width


def export(svg_path: Path, pdf: Path | None, png: Path | None, physical_width_mm: float, dpi: int) -> None:
    if not pdf and not png:
        return
    converter = shutil.which("rsvg-convert")
    if not converter:
        sys.exit("SVG was created, but rsvg-convert is required for PDF/PNG export")
    if pdf:
        pdf.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([converter, "-f", "pdf", "-o", str(pdf), str(svg_path)], check=True)
    if png:
        png.parent.mkdir(parents=True, exist_ok=True)
        width_px = max(1, round(physical_width_mm / 25.4 * dpi))
        subprocess.run(
            [converter, "-f", "png", "-w", str(width_px), "-o", str(png), str(svg_path)],
            check=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--out", type=Path, required=True, help="Output SVG")
    parser.add_argument("--pdf", type=Path)
    parser.add_argument("--png", type=Path)
    parser.add_argument("--dpi", type=int, default=180)
    args = parser.parse_args()
    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"cannot read spec {args.spec}: {exc}")
    svg, physical_width = compose(spec)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(svg, encoding="utf-8")
    try:
        export(args.out, args.pdf, args.png, physical_width, args.dpi)
    except subprocess.CalledProcessError as exc:
        sys.exit(f"export failed: {exc}")
    print(f"SVG  {args.out.resolve()}")
    if args.pdf:
        print(f"PDF  {args.pdf.resolve()}")
    if args.png:
        print(f"PNG  {args.png.resolve()}")


if __name__ == "__main__":
    main()
