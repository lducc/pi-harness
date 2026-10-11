#!/usr/bin/env python3
"""Build an editable draw.io paper figure from a paper-icons compatible JSON spec.

The generated draw.io XML keeps every card, label, connector, group, and icon
editable. Icons are loaded from the paper-icons catalog, recolored only when the
catalog allows it, and embedded as self-contained SVG data URIs.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote, unquote
from xml.etree import ElementTree as ET

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
SUPPORTED_COLUMNS = {"single", "double"}
SUPPORTED_LAYOUTS = {"pipeline", "grid", "freeform"}
SUPPORTED_SHAPES = {"round", "rect", "pill", "database", "circle"}
SUPPORTED_TONES = {
    "neutral",
    "accent",
    "secondary",
    "success",
    "warning",
    "danger",
}
ACADEMIC_STYLE_PATH = (
    Path(__file__).resolve().parent.parent / "assets/academic-style.yaml"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Figure JSON specification.")
    parser.add_argument("--out", type=Path, required=True, help="Output .drawio path.")
    parser.add_argument(
        "--paper-icons-skill",
        type=Path,
        help="Path to paper-icons; otherwise discover common skill locations.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Icon/source manifest path; defaults beside the .drawio file.",
    )
    parser.add_argument(
        "--paper-palette",
        type=Path,
        help=(
            "Paper-level palette contract. Overrides paper_palette.path in "
            "the figure spec and binds its ID and SHA-256 to the source."
        ),
    )
    return parser.parse_args()


def fail(message: str) -> None:
    raise SystemExit(message)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def normalize_hex(color: object) -> str:
    if not isinstance(color, str):
        raise ValueError(f"color must be a string, got {color!r}")
    raw = color.strip().lstrip("#")
    if len(raw) == 3:
        raw = "".join(character * 2 for character in raw)
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", raw):
        raise ValueError(f"invalid hex color {color!r}")
    return "#" + raw.upper()


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    raw = normalize_hex(color)[1:]
    return tuple(int(raw[index : index + 2], 16) for index in (0, 2, 4))


def blend(color: str, background: str = "#FFFFFF", amount: float = 0.91) -> str:
    front = hex_to_rgb(color)
    back = hex_to_rgb(background)
    mixed = [
        round(foreground * (1 - amount) + base * amount)
        for foreground, base in zip(front, back)
    ]
    return "#" + "".join(f"{channel:02X}" for channel in mixed)


def discover_paper_icons(explicit: Path | None) -> Path:
    candidates: list[Path] = []
    bundled = (
        Path(__file__).resolve().parent.parent
        / "assets/paper-icons"
    )
    if explicit:
        candidates.append(explicit.expanduser())
    if os.environ.get("PAPER_ICONS_SKILL"):
        candidates.append(Path(os.environ["PAPER_ICONS_SKILL"]).expanduser())
    candidates.extend(
        [
            Path.home() / ".agents/skills/paper-icons",
            Path.home() / ".claude/skills/paper-icons",
            Path.home() / ".codex/skills/paper-icons",
            bundled,
        ]
    )
    checked = []
    for candidate in candidates:
        resolved = candidate.resolve()
        checked.append(str(resolved))
        if (resolved / "library/catalog.json").is_file() and (
            (resolved / "SKILL.md").is_file()
            or resolved == bundled.resolve()
        ):
            return resolved
    fail(
        "paper-icons skill was not found. Pass --paper-icons-skill or set "
        "PAPER_ICONS_SKILL. Checked:\n- " + "\n- ".join(checked)
    )


def read_catalog(skill_root: Path) -> dict[str, dict]:
    path = skill_root / "library/catalog.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return {entry["id"]: entry for entry in payload["icons"]}
    except (OSError, KeyError, json.JSONDecodeError, TypeError) as exc:
        fail(f"cannot read paper-icons catalog {path}: {exc}")


def read_academic_style() -> dict:
    try:
        payload = json.loads(ACADEMIC_STYLE_PATH.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise TypeError("root must be an object")
        return payload
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        fail(f"cannot read academic style {ACADEMIC_STYLE_PATH}: {exc}")


def read_paper_palette(path: Path, academic_style: dict) -> tuple[dict, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read paper palette {path}: {exc}")
    if not isinstance(payload, dict):
        fail(f"paper palette {path} root must be an object")
    expected_schema = int(
        academic_style["color"]["paper_palette_schema_version"]
    )
    if payload.get("schema_version") != expected_schema:
        fail(
            f"paper palette {path} schema_version must be "
            f"{expected_schema}"
        )
    palette_id = payload.get("palette_id")
    if not isinstance(palette_id, str) or not palette_id.strip():
        fail(f"paper palette {path} requires a non-empty palette_id")
    status = payload.get("status", "draft")
    if status not in {"draft", "frozen"}:
        fail(f"paper palette {path} status must be draft or frozen")
    paper_id = payload.get("paper_id", "")
    if not isinstance(paper_id, str):
        fail(f"paper palette {path} paper_id must be text")
    semantic = payload.get("semantic")
    if not isinstance(semantic, dict):
        fail(f"paper palette {path} semantic must be an object")
    missing = sorted(set(DEFAULT_PALETTE) - set(semantic))
    if missing:
        fail(
            f"paper palette {path} is missing semantic roles: "
            + ", ".join(missing)
        )
    extra = sorted(set(semantic) - set(DEFAULT_PALETTE))
    if extra:
        fail(
            f"paper palette {path} has unsupported semantic roles: "
            + ", ".join(extra)
        )
    try:
        normalized_semantic = {
            key: normalize_hex(value)
            for key, value in semantic.items()
        }
        chart_roles = payload.get("chart_roles", {})
        if not isinstance(chart_roles, dict):
            raise ValueError("chart_roles must be an object")
        normalized_chart_roles = {
            key: normalize_hex(value)
            for key, value in chart_roles.items()
        }
    except ValueError as exc:
        fail(f"invalid paper palette {path}: {exc}")
    unknown_chart_colors = sorted(
        set(normalized_chart_roles.values())
        - set(normalized_semantic.values())
    )
    if unknown_chart_colors:
        fail(
            f"paper palette {path} chart roles use colors outside semantic "
            "roles: " + ", ".join(unknown_chart_colors)
        )
    neutral_roles = {"canvas", "ink", "muted", "stroke", "neutral"}
    chromatic_colors = {
        value
        for role, value in normalized_semantic.items()
        if role not in neutral_roles
    }
    maximum_hues = int(academic_style["color"]["maximum_semantic_hues"])
    if len(chromatic_colors) > maximum_hues:
        fail(
            f"paper palette {path} uses {len(chromatic_colors)} semantic "
            f"hues; maximum is {maximum_hues}"
        )
    rules = payload.get("rules")
    if not isinstance(rules, dict):
        fail(f"paper palette {path} rules must be an object")
    if rules.get("maximum_semantic_hues") != maximum_hues:
        fail(
            f"paper palette {path} rules.maximum_semantic_hues must be "
            f"{maximum_hues}"
        )
    payload = dict(payload)
    payload["semantic"] = normalized_semantic
    payload["chart_roles"] = normalized_chart_roles
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return payload, hashlib.sha256(canonical).hexdigest()


def resolve_paper_palette_path(
    spec: dict,
    spec_path: Path,
    explicit: Path | None,
) -> Path | None:
    if explicit:
        return explicit.expanduser().resolve()
    config = spec.get("paper_palette")
    if config is None:
        return None
    if not isinstance(config, dict):
        fail("paper_palette must be an object")
    raw_path = config.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        fail("paper_palette.path requires non-empty text")
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = spec_path.parent / candidate
    return candidate.resolve()


def recolor_svg(markup: str, target: str) -> str:
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


def icon_data_uri(
    entry: dict,
    skill_root: Path,
    color: str,
) -> tuple[str, str]:
    relative = entry.get("svg")
    if not relative:
        raise ValueError(f"icon {entry.get('id')!r} has no SVG source")
    path = (skill_root / relative).resolve()
    try:
        markup = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read icon SVG {path}: {exc}") from exc
    markup = re.sub(r"<\?xml[^>]*\?>", "", markup, flags=re.IGNORECASE).strip()
    if not re.search(r"<svg\b", markup, re.IGNORECASE):
        raise ValueError(f"icon {entry.get('id')!r} is not an SVG document")
    if entry.get("recolorable"):
        markup = recolor_svg(markup, color)
    portable_source = "paper-icons://" + str(relative).replace("\\", "/")
    return "data:image/svg+xml," + quote(markup, safe=""), portable_source


def icon_family(entry: dict, icon_id: str) -> str:
    category = str(entry.get("category", "")).casefold()
    if category == "fetched":
        return "lucide"
    if category in {"lucide", "tabler", "phosphor", "duotone", "brand"}:
        return category
    relative = str(entry.get("svg", "")).replace("\\", "/")
    match = re.search(
        r"/(lucide|tabler|phosphor|duotone|brand|fetched)/",
        f"/{relative}",
        flags=re.IGNORECASE,
    )
    if match:
        family = match.group(1).casefold()
        return "lucide" if family == "fetched" else family
    return "original"


def load_spec(path: Path) -> dict:
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read figure spec {path}: {exc}")
    if not isinstance(spec, dict):
        fail("figure spec must be a JSON object")
    return spec


def validate_spec(spec: dict, catalog: dict[str, dict]) -> None:
    errors: list[str] = []
    metadata = spec.get("metadata", {})
    if not isinstance(metadata, dict):
        errors.append("metadata must be an object")
        metadata = {}
    for field in ("title", "description", "claim"):
        if (
            not isinstance(metadata.get(field), str)
            or not metadata[field].strip()
        ):
            errors.append(f"metadata.{field} requires non-empty text")
    figure = spec.get("figure", {})
    if not isinstance(figure, dict):
        errors.append("figure must be an object")
        figure = {}
    column = figure.get("column", "double")
    if not isinstance(column, str) or column not in SUPPORTED_COLUMNS:
        errors.append("figure.column must be single or double")
    layout = figure.get("layout", "pipeline")
    if not isinstance(layout, str) or layout not in SUPPORTED_LAYOUTS:
        errors.append(
            "figure.layout must be one of " + ", ".join(sorted(SUPPORTED_LAYOUTS))
        )
    direction = figure.get("direction", "horizontal")
    if not isinstance(direction, str) or direction not in {
        "horizontal",
        "vertical",
    }:
        errors.append("figure.direction must be horizontal or vertical")
    if not isinstance(figure.get("palette", {}), dict):
        errors.append("figure.palette must be an object")
    paper_palette = spec.get("paper_palette")
    if paper_palette is not None:
        if not isinstance(paper_palette, dict):
            errors.append("paper_palette must be an object")
        elif (
            not isinstance(paper_palette.get("path"), str)
            or not paper_palette["path"].strip()
        ):
            errors.append("paper_palette.path requires non-empty text")

    raw_nodes = spec.get("nodes", [])
    if not isinstance(raw_nodes, list) or not raw_nodes:
        errors.append("at least one node is required")
        raw_nodes = []
    nodes = [node for node in raw_nodes if isinstance(node, dict)]
    node_ids = [node.get("id") for node in nodes]
    if len(node_ids) != len(raw_nodes):
        errors.append("every node must be an object")
    valid_node_ids = [
        node_id
        for node_id in node_ids
        if isinstance(node_id, str) and node_id
    ]
    if len(valid_node_ids) != len(node_ids):
        errors.append("every node requires a non-empty string id")
    if len(valid_node_ids) != len(set(valid_node_ids)):
        errors.append("node ids must be unique")
    valid_ids = set(valid_node_ids)
    id_pattern = re.compile(r"[A-Za-z][A-Za-z0-9_.-]*")
    for node in nodes:
        node_id = node.get("id")
        if isinstance(node_id, str) and not id_pattern.fullmatch(node_id):
            errors.append(f"invalid node id {node_id!r}")
        if (
            not isinstance(node.get("label"), str)
            or not node["label"].strip()
        ):
            errors.append(f"node {node_id!r} requires label")
        if node.get("subtitle") is not None and not isinstance(
            node["subtitle"],
            str,
        ):
            errors.append(f"node {node_id!r} subtitle must be text")
        icon = node.get("icon")
        if icon and (not isinstance(icon, str) or icon not in catalog):
            errors.append(
                f"node {node_id!r} references unknown icon {icon!r}"
            )
        tone = node.get("tone", "neutral")
        if not isinstance(tone, str) or tone not in SUPPORTED_TONES:
            errors.append(f"node {node_id!r} has unsupported tone")
        shape = node.get("shape", "round")
        if not isinstance(shape, str) or shape not in SUPPORTED_SHAPES:
            errors.append(f"node {node_id!r} has unsupported shape")
        icon_position = node.get("icon_position", "auto")
        if not isinstance(icon_position, str) or icon_position not in {
            "auto",
            "top",
            "left",
        }:
            errors.append(f"node {node_id!r} has unsupported icon_position")
        if layout == "freeform" and any(
            key not in node for key in ("x", "y", "w", "h")
        ):
            errors.append(
                f"freeform node {node_id!r} requires x, y, w, and h"
            )
        elif layout == "freeform":
            for key in ("x", "y", "w", "h"):
                try:
                    numeric(node[key], f"{node_id}.{key}")
                except ValueError as exc:
                    errors.append(str(exc))

    raw_groups = spec.get("groups", [])
    if not isinstance(raw_groups, list):
        errors.append("groups must be a list")
        raw_groups = []
    groups = [group for group in raw_groups if isinstance(group, dict)]
    group_ids = [group.get("id") for group in groups]
    if len(group_ids) != len(raw_groups):
        errors.append("every group must be an object")
    valid_group_ids = [
        group_id
        for group_id in group_ids
        if isinstance(group_id, str) and group_id
    ]
    if len(valid_group_ids) != len(group_ids):
        errors.append("every group requires a non-empty string id")
    if len(valid_group_ids) != len(set(valid_group_ids)):
        errors.append("group ids must be unique")
    valid_groups = set(valid_group_ids)
    for group in groups:
        group_id = group.get("id")
        if isinstance(group_id, str) and not id_pattern.fullmatch(group_id):
            errors.append(f"invalid group id {group_id!r}")
        if (
            not isinstance(group.get("label"), str)
            or not group["label"].strip()
        ):
            errors.append(f"group {group_id!r} requires label")
        group_tone = group.get("tone", "neutral")
        if (
            not isinstance(group_tone, str)
            or group_tone not in SUPPORTED_TONES
        ):
            errors.append(f"group {group_id!r} has unsupported tone")
    for node in nodes:
        group_id = node.get("group")
        if group_id and (
            not isinstance(group_id, str) or group_id not in valid_groups
        ):
            errors.append(
                f"node {node.get('id')!r} references unknown group "
                f"{group_id!r}"
            )

    raw_edges = spec.get("edges", [])
    if not isinstance(raw_edges, list):
        errors.append("edges must be a list")
        raw_edges = []
    edges = [edge for edge in raw_edges if isinstance(edge, dict)]
    if len(edges) != len(raw_edges):
        errors.append("every edge must be an object")
    for index, edge in enumerate(edges):
        source, target = edge.get("from"), edge.get("to")
        if (
            not isinstance(source, str)
            or not isinstance(target, str)
            or source not in valid_ids
            or target not in valid_ids
        ):
            errors.append(f"edge {index} references an unknown node")
        edge_style = edge.get("style", "solid")
        if not isinstance(edge_style, str) or edge_style not in {
            "solid",
            "dashed",
        }:
            errors.append(f"edge {index} has unsupported style")
        route = edge.get("route", "orthogonal")
        if not isinstance(route, str) or route not in {
            "orthogonal",
            "straight",
            "curve",
        }:
            errors.append(f"edge {index} has unsupported route")
        edge_tone = edge.get("tone", "neutral")
        if (
            not isinstance(edge_tone, str)
            or edge_tone not in SUPPORTED_TONES
        ):
            errors.append(f"edge {index} has unsupported tone")
        arrow = edge.get("arrow", "end")
        if not isinstance(arrow, str) or arrow not in {
            "end",
            "both",
            "none",
        }:
            errors.append(f"edge {index} has unsupported arrow")
        for field in ("label", "relation"):
            if edge.get(field) is not None and not isinstance(
                edge[field],
                str,
            ):
                errors.append(f"edge {index}.{field} must be text")
        if (
            not isinstance(edge.get("relation"), str)
            or not edge["relation"].strip()
        ):
            errors.append(f"edge {index}.relation requires non-empty text")
        for field in ("entry", "exit"):
            if field not in edge:
                continue
            port = edge[field]
            if not isinstance(port, (list, tuple)) or len(port) != 2:
                errors.append(f"edge {index}.{field} requires [x, y]")
                continue
            try:
                port_x = numeric(port[0], f"edge {index}.{field}[0]")
                port_y = numeric(port[1], f"edge {index}.{field}[1]")
            except ValueError as exc:
                errors.append(str(exc))
            else:
                if not 0 <= port_x <= 1 or not 0 <= port_y <= 1:
                    errors.append(
                        f"edge {index}.{field} coordinates must be in [0, 1]"
                    )
        if "points" in edge:
            points = edge["points"]
            if not isinstance(points, list):
                errors.append(f"edge {index}.points must be a list")
            else:
                for point_index, point in enumerate(points):
                    if not isinstance(point, (list, tuple)) or len(point) != 2:
                        errors.append(
                            f"edge {index}.points[{point_index}] "
                            "requires [x, y]"
                        )
                        continue
                    for coordinate_index, coordinate in enumerate(point):
                        try:
                            numeric(
                                coordinate,
                                f"edge {index}.points[{point_index}]"
                                f"[{coordinate_index}]",
                            )
                        except ValueError as exc:
                            errors.append(str(exc))

    raw_annotations = spec.get("annotations", [])
    if not isinstance(raw_annotations, list):
        errors.append("annotations must be a list")
        raw_annotations = []
    annotations = [
        annotation for annotation in raw_annotations if isinstance(annotation, dict)
    ]
    if len(annotations) != len(raw_annotations):
        errors.append("every annotation must be an object")
    for index, annotation in enumerate(annotations):
        for field in ("x", "y", "text"):
            if field not in annotation:
                errors.append(f"annotation {index} requires {field}")
        if "text" in annotation and not isinstance(annotation["text"], str):
            errors.append(f"annotation {index}.text must be text")
        for field in ("x", "y", "w", "h"):
            if field in annotation:
                try:
                    numeric(
                        annotation[field],
                        f"annotation {index}.{field}",
                    )
                except ValueError as exc:
                    errors.append(str(exc))
        annotation_tone = annotation.get("tone", "accent")
        if (
            not isinstance(annotation_tone, str)
            or annotation_tone not in SUPPORTED_TONES
        ):
            errors.append(f"annotation {index} has unsupported tone")
    if errors:
        fail("invalid figure spec:\n- " + "\n- ".join(errors))


def numeric(value: object, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric, got {value!r}") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite, got {value!r}")
    return number


def layout_nodes(
    spec: dict,
    academic_style: dict,
) -> tuple[dict[str, dict], float, float, str, float]:
    figure = spec.get("figure", {})
    column = figure.get("column", "double")
    default_width, default_height = (
        float(value)
        for value in academic_style["geometry"]["default_canvas"][column]
    )
    width = numeric(figure.get("width", default_width), "figure.width")
    height = numeric(figure.get("height", default_height), "figure.height")
    if width <= 0 or height <= 0:
        raise ValueError("figure width and height must be positive")
    layout = figure.get("layout", "pipeline")
    direction = figure.get("direction", "horizontal")
    nodes = [dict(node) for node in spec["nodes"]]
    geometry: dict[str, dict] = {}

    if layout == "freeform":
        for node in nodes:
            geometry[node["id"]] = {
                **node,
                "x": numeric(node["x"], f"{node['id']}.x"),
                "y": numeric(node["y"], f"{node['id']}.y"),
                "w": numeric(node["w"], f"{node['id']}.w"),
                "h": numeric(node["h"], f"{node['id']}.h"),
            }
    elif layout == "pipeline":
        count = len(nodes)
        if direction == "horizontal":
            margin = 40.0
            gap = 40.0 if count <= 5 else 28.0
            node_width = min(
                180.0,
                (width - 2 * margin - gap * max(0, count - 1)) / count,
            )
            # Reserve enough vertical space for an icon plus a two-line title
            # and two-line subtitle at publication-safe type sizes. The former
            # 150 px default clipped common labels such as
            # “Task specification / Operator + constraints” after Draw.io
            # rendering at double-column width.
            node_height = 170.0
            if node_width < 140:
                raise ValueError(
                    "pipeline nodes would be narrower than 140 px; use a larger "
                    "canvas, vertical direction, or fewer stages"
                )
            total = count * node_width + max(0, count - 1) * gap
            start_x = (width - total) / 2
            y = max(70.0, height * 0.43 - node_height / 2)
            for index, node in enumerate(nodes):
                geometry[node["id"]] = {
                    **node,
                    "x": start_x + index * (node_width + gap),
                    "y": y,
                    "w": node_width,
                    "h": node_height,
                }
        else:
            margin = 50.0
            gap = 48.0
            node_width = min(260.0, width - 2 * margin)
            node_height = min(
                92.0,
                (height - 2 * margin - gap * max(0, count - 1)) / count,
            )
            if node_height < 72:
                raise ValueError(
                    "vertical pipeline nodes would be shorter than 72 px; "
                    "increase canvas height or use fewer stages"
                )
            total = count * node_height + max(0, count - 1) * gap
            x = (width - node_width) / 2
            start_y = (height - total) / 2
            for index, node in enumerate(nodes):
                geometry[node["id"]] = {
                    **node,
                    "x": x,
                    "y": start_y + index * (node_height + gap),
                    "w": node_width,
                    "h": node_height,
                }
    else:
        columns = int(figure.get("columns", min(3, len(nodes))))
        if columns < 1:
            raise ValueError("figure.columns must be at least 1")
        rows = (len(nodes) + columns - 1) // columns
        margin_x, margin_y = 60.0, 60.0
        gap_x, gap_y = 50.0, 48.0
        node_width = min(
            210.0,
            (width - 2 * margin_x - gap_x * max(0, columns - 1)) / columns,
        )
        node_height = min(
            100.0,
            (height - 2 * margin_y - gap_y * max(0, rows - 1)) / rows,
        )
        if node_width < 130 or node_height < 70:
            raise ValueError(
                "grid cells are too small; increase canvas or reduce panels"
            )
        total_width = columns * node_width + max(0, columns - 1) * gap_x
        total_height = rows * node_height + max(0, rows - 1) * gap_y
        start_x = (width - total_width) / 2
        start_y = (height - total_height) / 2
        for index, node in enumerate(nodes):
            row, column_index = divmod(index, columns)
            geometry[node["id"]] = {
                **node,
                "x": start_x + column_index * (node_width + gap_x),
                "y": start_y + row * (node_height + gap_y),
                "w": node_width,
                "h": node_height,
            }

    source_nodes = {node["id"]: node for node in nodes}
    for node_id, node in geometry.items():
        source_node = source_nodes[node_id]
        for key in ("x", "y", "w", "h"):
            if key in source_node:
                node[key] = numeric(
                    source_node[key],
                    f"{node_id}.{key}",
                )
        if node["w"] <= 0 or node["h"] <= 0:
            raise ValueError(f"node {node_id!r} must have positive width and height")
        if node.get("shape") == "circle" and abs(node["w"] - node["h"]) > 0.1:
            size = min(node["w"], node["h"])
            node["x"] += (node["w"] - size) / 2
            node["y"] += (node["h"] - size) / 2
            node["w"] = node["h"] = size
        if (
            node["x"] < 0
            or node["y"] < 0
            or node["x"] + node["w"] > width
            or node["y"] + node["h"] > height
        ):
            raise ValueError(f"node {node_id!r} lies outside the canvas")
    for edge_index, edge in enumerate(spec.get("edges", [])):
        for point_index, point in enumerate(edge.get("points", [])):
            point_x = numeric(
                point[0],
                f"edge {edge_index}.points[{point_index}][0]",
            )
            point_y = numeric(
                point[1],
                f"edge {edge_index}.points[{point_index}][1]",
            )
            if not 0 <= point_x <= width or not 0 <= point_y <= height:
                raise ValueError(
                    f"edge {edge_index}.points[{point_index}] "
                    "lies outside the canvas"
                )
    physical_width_mm = float(
        academic_style["geometry"][f"{column}_column_width_mm"]
    )
    return geometry, width, height, column, physical_width_mm


def add_geometry(
    cell: ET.Element,
    *,
    x: float = 0,
    y: float = 0,
    width: float = 0,
    height: float = 0,
    relative: bool = False,
) -> ET.Element:
    attributes = {"as": "geometry"}
    if relative:
        attributes["relative"] = "1"
    else:
        attributes.update(
            {
                "x": f"{x:.1f}",
                "y": f"{y:.1f}",
                "width": f"{width:.1f}",
                "height": f"{height:.1f}",
            }
        )
    return ET.SubElement(cell, "mxGeometry", attributes)


def topological_side(source: dict, target: dict) -> tuple[str, str]:
    source_center = (source["x"] + source["w"] / 2, source["y"] + source["h"] / 2)
    target_center = (target["x"] + target["w"] / 2, target["y"] + target["h"] / 2)
    dx = target_center[0] - source_center[0]
    dy = target_center[1] - source_center[1]
    if abs(dx) >= abs(dy):
        return ("east", "west") if dx >= 0 else ("west", "east")
    return ("south", "north") if dy >= 0 else ("north", "south")


def port_for(side: str, fraction: float) -> tuple[float, float]:
    if side == "east":
        return 1.0, fraction
    if side == "west":
        return 0.0, fraction
    if side == "north":
        return fraction, 0.0
    return fraction, 1.0


def distributed_ports(
    edges: list[dict],
    geometry: dict[str, dict],
) -> dict[tuple[int, str], tuple[float, float]]:
    membership: dict[tuple[str, str], list[tuple[int, str]]] = defaultdict(list)
    sides: dict[tuple[int, str], str] = {}
    for index, edge in enumerate(edges):
        source_side, target_side = topological_side(
            geometry[edge["from"]], geometry[edge["to"]]
        )
        for role, node_id, side in (
            ("source", edge["from"], source_side),
            ("target", edge["to"], target_side),
        ):
            sides[(index, role)] = side
            membership[(node_id, side)].append((index, role))
    ports: dict[tuple[int, str], tuple[float, float]] = {}
    for members in membership.values():
        count = len(members)
        fractions = [(position + 1) / (count + 1) for position in range(count)]
        for member, fraction in zip(members, fractions):
            ports[member] = port_for(sides[member], fraction)
    return ports


def node_shape_style(shape: str) -> str:
    if shape == "database":
        return "shape=cylinder3;boundedLbl=1;backgroundOutline=1;"
    if shape == "circle":
        return "ellipse;aspect=fixed;"
    if shape == "rect":
        return "rounded=0;"
    if shape == "pill":
        return "rounded=1;arcSize=50;"
    return "rounded=1;arcSize=14;"


def build_figure(
    spec: dict,
    geometry: dict[str, dict],
    width: float,
    height: float,
    column: str,
    physical_width_mm: float,
    skill_root: Path,
    catalog: dict[str, dict],
    academic_style: dict,
    paper_palette: dict | None = None,
    paper_palette_digest: str | None = None,
) -> tuple[ET.ElementTree, list[dict]]:
    palette = dict(academic_style["color"]["palette"])
    for key, value in DEFAULT_PALETTE.items():
        palette.setdefault(key, value)
    local_palette = spec.get("figure", {}).get("palette", {})
    if paper_palette is not None:
        paper_semantic = paper_palette["semantic"]
        for key, value in local_palette.items():
            if (
                key not in paper_semantic
                or normalize_hex(value) != paper_semantic[key]
            ):
                raise ValueError(
                    "figure.palette cannot drift from the bound paper "
                    f"palette at role {key!r}"
                )
        palette.update(paper_semantic)
    else:
        palette.update(local_palette)
    palette = {
        key: normalize_hex(value)
        for key, value in palette.items()
    }
    minimum_final_text_pt = float(
        academic_style["typography"]["minimum_final_text_pt"]
    )
    font_family = str(academic_style["typography"]["primary_family"])

    def pixels_for_final_points(points: float) -> int:
        return math.ceil(
            points
            * width
            * 25.4
            / (physical_width_mm * 72.0)
            - 1e-9
        )

    secondary_font_px = pixels_for_final_points(minimum_final_text_pt)
    body_font_px = pixels_for_final_points(
        float(academic_style["typography"]["preferred_body_pt"][0])
    )
    panel_font_px = pixels_for_final_points(
        float(
            academic_style["typography"]["preferred_panel_label_pt"][0]
        )
    )
    fonts = {
        "node": body_font_px,
        "label": body_font_px,
        "secondary": secondary_font_px,
        "edge": secondary_font_px,
        "group": body_font_px,
        "badge": secondary_font_px,
        "annotation": secondary_font_px,
        "panel": panel_font_px,
    }
    pixels_per_point = width * 25.4 / (physical_width_mm * 72.0)
    supporting_stroke_pt = (
        float(academic_style["stroke"]["minimum_supporting_pt"])
        + float(academic_style["stroke"]["primary_range_pt"][0])
    ) / 2
    primary_stroke_pt = sum(
        float(value)
        for value in academic_style["stroke"]["primary_range_pt"]
    ) / 2
    supporting_stroke_px = supporting_stroke_pt * pixels_per_point
    primary_stroke_px = primary_stroke_pt * pixels_per_point
    figure_config = spec.get("figure", {})
    default_icon_position = (
        "left"
        if figure_config.get("layout", "pipeline") == "pipeline"
        and figure_config.get("direction", "horizontal") == "vertical"
        else "top"
    )
    metadata = spec["metadata"]
    used_tones = {
        item.get("tone", default)
        for items, default in (
            (spec.get("nodes", []), "neutral"),
            (spec.get("edges", []), "neutral"),
            (spec.get("groups", []), "neutral"),
            (spec.get("annotations", []), "accent"),
        )
        for item in items
        if isinstance(item, dict)
    }
    semantic_colors = sorted(
        {palette[tone] for tone in used_tones if tone != "neutral"}
    )
    digest = hashlib.sha256(
        (metadata["title"] + metadata["description"]).encode("utf-8")
    ).hexdigest()[:12]
    mxfile = ET.Element(
        "mxfile",
        {
            "host": "app.diagrams.net",
            "version": "26.0.0",
            "type": "device",
            "data-title": metadata["title"],
            "data-description": metadata["description"],
            "data-claim": metadata["claim"],
            "data-column": column,
            "data-width-mm": f"{physical_width_mm:.1f}",
            "data-academic-style-version": str(academic_style.get("version", 1)),
            "data-minimum-text-pt": f"{minimum_final_text_pt:g}",
            "data-semantic-colors": ",".join(semantic_colors),
            "data-semantic-color-count": str(len(semantic_colors)),
        },
    )
    if paper_palette is not None:
        if not paper_palette_digest:
            raise ValueError("paper palette digest is missing")
        mxfile.set("data-paper-palette-bound", "1")
        mxfile.set(
            "data-paper-palette-schema",
            str(paper_palette["schema_version"]),
        )
        mxfile.set("data-paper-palette-id", paper_palette["palette_id"])
        mxfile.set("data-paper-palette-sha256", paper_palette_digest)
        mxfile.set("data-paper-palette-status", paper_palette["status"])
        if paper_palette.get("paper_id"):
            mxfile.set("data-paper-id", paper_palette["paper_id"])
    diagram = ET.SubElement(
        mxfile,
        "diagram",
        {"id": f"figure-{digest}", "name": metadata.get("page_name", "Figure")},
    )
    model = ET.SubElement(
        diagram,
        "mxGraphModel",
        {
            "dx": "1000",
            "dy": "700",
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": f"{width:.0f}",
            "pageHeight": f"{height:.0f}",
            "math": "0",
            "shadow": "0",
            "background": palette["canvas"],
        },
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
    canvas_cell = ET.SubElement(
        root,
        "mxCell",
        {
            "id": "canvas-bounds",
            "value": "",
            "style": (
                f"rect;html=1;fillColor={palette['canvas']};"
                "strokeColor=none;"
                "pointerEvents=0;movable=0;resizable=0;connectable=0;"
            ),
            "vertex": "1",
            "connectable": "0",
            "parent": "1",
            "data-canvas-boundary": "1",
        },
    )
    add_geometry(
        canvas_cell,
        x=0,
        y=0,
        width=width,
        height=height,
    )

    groups = spec.get("groups", [])
    group_geometry: dict[str, dict] = {}
    for group in groups:
        members = [
            node for node in geometry.values() if node.get("group") == group["id"]
        ]
        if not members:
            continue
        padding_x, top_padding, bottom_padding = 24.0, 42.0, 24.0
        min_x = min(node["x"] for node in members) - padding_x
        min_y = min(node["y"] for node in members) - top_padding
        max_x = max(node["x"] + node["w"] for node in members) + padding_x
        max_y = max(node["y"] + node["h"] for node in members) + bottom_padding
        min_x, min_y = max(0.0, min_x), max(0.0, min_y)
        tone = group.get("tone", "neutral")
        color = palette[tone]
        fill = blend(color, palette["canvas"], 0.95)
        group_geometry[group["id"]] = {
            "x": min_x,
            "y": min_y,
            "w": max_x - min_x,
            "h": max_y - min_y,
        }
        style = (
            "swimlane;startSize=30;horizontal=1;html=1;whiteSpace=wrap;"
            "container=1;collapsible=0;recursiveResize=0;pointerEvents=0;"
            f"fillColor={fill};strokeColor={color};fontColor={palette['ink']};"
            f"fontFamily={font_family};fontSize={fonts['group']};"
            f"fontStyle=1;rounded=0;strokeWidth={supporting_stroke_px:.2f};"
            + ("dashed=1;dashPattern=6 4;" if group.get("style") == "dashed" else "")
        )
        cell = ET.SubElement(
            root,
            "mxCell",
            {
                "id": f"group-{group['id']}",
                "value": group["label"],
                "style": style,
                "vertex": "1",
                "parent": "1",
                "data-group": "1",
            },
        )
        add_geometry(
            cell,
            x=min_x,
            y=min_y,
            width=max_x - min_x,
            height=max_y - min_y,
        )

    edges = spec.get("edges", [])
    ports = distributed_ports(edges, geometry)
    for index, edge in enumerate(edges, start=1):
        tone = edge.get("tone", "neutral")
        color = palette[tone]
        route = edge.get("route", "orthogonal")
        if route == "straight":
            route_style = "edgeStyle=none;"
        elif route == "curve":
            route_style = "edgeStyle=orthogonalEdgeStyle;curved=1;"
        else:
            route_style = "edgeStyle=orthogonalEdgeStyle;"
        arrow = edge.get("arrow", "end")
        arrow_style = {
            "end": "endArrow=block;endFill=1;startArrow=none;",
            "both": "endArrow=block;endFill=1;startArrow=block;startFill=1;",
            "none": "endArrow=none;startArrow=none;",
        }.get(arrow)
        if arrow_style is None:
            raise ValueError(f"edge {index - 1} has unsupported arrow {arrow!r}")
        source_port = tuple(edge.get("exit", ports[(index - 1, "source")]))
        target_port = tuple(edge.get("entry", ports[(index - 1, "target")]))
        if len(source_port) != 2 or len(target_port) != 2:
            raise ValueError(f"edge {index - 1} entry/exit must contain x and y")
        dashed = (
            "dashed=1;dashPattern=6 4;"
            if edge.get("style", "solid") == "dashed"
            else ""
        )
        style = (
            f"{route_style}rounded=1;orthogonalLoop=1;jettySize=auto;html=1;"
            f"strokeColor={color};strokeWidth={primary_stroke_px:.2f};"
            f"{arrow_style}{dashed}"
            f"fontFamily={font_family};fontSize={fonts['edge']};"
            f"fontColor={palette['muted']};"
            f"labelBackgroundColor={palette['canvas']};"
            f"exitX={float(source_port[0]):.3f};exitY={float(source_port[1]):.3f};"
            "exitDx=0;exitDy=0;"
            f"entryX={float(target_port[0]):.3f};entryY={float(target_port[1]):.3f};"
            "entryDx=0;entryDy=0;"
        )
        cell = ET.SubElement(
            root,
            "mxCell",
            {
                "id": f"edge-{index}",
                "value": edge.get("label", ""),
                "style": style,
                "edge": "1",
                "parent": "1",
                "source": f"node-{edge['from']}",
                "target": f"node-{edge['to']}",
                "data-relation": edge.get("relation", ""),
            },
        )
        edge_geometry = add_geometry(cell, relative=True)
        edge_geometry.set("x", "0")
        edge_geometry.set("y", "-12")
        if edge.get("points"):
            points = ET.SubElement(edge_geometry, "Array", {"as": "points"})
            for point in edge["points"]:
                if len(point) != 2:
                    raise ValueError("edge waypoint must contain x and y")
                ET.SubElement(
                    points,
                    "mxPoint",
                    {"x": str(float(point[0])), "y": str(float(point[1]))},
                )

    icon_manifest: list[dict] = []
    for node in geometry.values():
        tone = node.get("tone", "neutral")
        color = palette[tone]
        fill = blend(color, palette["canvas"])
        shape = node.get("shape", "round")
        parent = "1"
        local_x, local_y = node["x"], node["y"]
        if node.get("group") and node["group"] in group_geometry:
            parent = f"group-{node['group']}"
            group = group_geometry[node["group"]]
            local_x = node["x"] - group["x"]
            local_y = node["y"] - group["y"]
        style = (
            f"{node_shape_style(shape)}whiteSpace=wrap;html=1;container=1;"
            "recursiveResize=0;collapsible=0;shadow=0;glass=0;"
            f"fillColor={fill};strokeColor={color};"
            f"strokeWidth={supporting_stroke_px:.2f};"
            f"fontColor={palette['ink']};fontFamily={font_family};"
            f"fontSize={fonts['node']};"
            "align=center;verticalAlign=middle;"
        )
        cell = ET.SubElement(
            root,
            "mxCell",
            {
                "id": f"node-{node['id']}",
                "value": "",
                "style": style,
                "vertex": "1",
                "parent": parent,
                "data-node": "1",
                "data-kind": node.get("kind", "entity"),
                "data-icon": node.get("icon", ""),
            },
        )
        add_geometry(
            cell,
            x=local_x,
            y=local_y,
            width=node["w"],
            height=node["h"],
        )

        icon_id = node.get("icon")
        icon_fraction_min, icon_fraction_max = (
            float(value)
            for value in academic_style["icons"][
                "size_fraction_of_node_height"
            ]
        )
        icon_fraction = (icon_fraction_min + icon_fraction_max) / 2
        icon_size = node["h"] * icon_fraction
        text_x = 12.0
        text_y = 12.0
        text_width = max(20.0, node["w"] - 24.0)
        text_height = max(20.0, node["h"] - 24.0)
        text_align = "center"
        text_vertical_align = "middle"
        if icon_id:
            entry = catalog[icon_id]
            family = icon_family(entry, icon_id)
            data_uri, source_path = icon_data_uri(entry, skill_root, color)
            payload = unquote(data_uri.split(",", 1)[1])
            payload_sha256 = hashlib.sha256(
                payload.encode("utf-8")
            ).hexdigest()
            icon_cell = ET.SubElement(
                root,
                "mxCell",
                {
                    "id": f"icon-{node['id']}",
                    "value": "",
                    "style": (
                        "shape=image;html=1;imageAspect=0;aspect=fixed;"
                        "strokeColor=none;fillColor=none;connectable=0;"
                        f"image={data_uri};"
                    ),
                    "vertex": "1",
                    "connectable": "0",
                    "parent": f"node-{node['id']}",
                    "data-icon-id": icon_id,
                    "data-icon-family": family,
                },
            )
            icon_position = node.get("icon_position", "auto")
            if icon_position == "auto":
                icon_position = default_icon_position
            if icon_position == "left":
                add_geometry(
                    icon_cell,
                    x=14.0,
                    y=(node["h"] - icon_size) / 2,
                    width=icon_size,
                    height=icon_size,
                )
                text_x = 14.0 + icon_size + 10.0
                text_y = 8.0
                text_width = max(20.0, node["w"] - text_x - 12.0)
                text_height = max(20.0, node["h"] - 16.0)
                text_align = "left"
                text_vertical_align = "middle"
            else:
                add_geometry(
                    icon_cell,
                    x=(node["w"] - icon_size) / 2,
                    y=12.0,
                    width=icon_size,
                    height=icon_size,
                )
                text_y = 12.0 + icon_size + 8.0
                text_height = max(20.0, node["h"] - text_y - 10.0)
                text_vertical_align = "top"
            icon_manifest.append(
                {
                    "node_id": node["id"],
                    "icon_id": icon_id,
                    "family": family,
                    "name": entry.get("name", ""),
                    "source": entry.get("source", ""),
                    "source_svg": source_path,
                    "catalog_svg": entry.get("svg", ""),
                    "recolorable": bool(entry.get("recolorable")),
                    "embedded": True,
                    "payload_sha256": payload_sha256,
                    "applied_color": color if entry.get("recolorable") else None,
                }
            )

        label = f"<b>{esc(node['label'])}</b>"
        if node.get("subtitle"):
            label += (
                f"<br><font color=\"{palette['muted']}\" "
                f"style=\"font-size:{fonts['secondary']}px\">"
                f"{esc(node['subtitle'])}</font>"
            )
        text_cell = ET.SubElement(
            root,
            "mxCell",
            {
                "id": f"label-{node['id']}",
                "value": label,
                "style": (
                    "text;html=1;strokeColor=none;fillColor=none;"
                    f"whiteSpace=wrap;overflow=hidden;align={text_align};"
                    f"verticalAlign={text_vertical_align};spacing=0;connectable=0;"
                    f"fontColor={palette['ink']};fontFamily={font_family};"
                    f"fontSize={fonts['label']};"
                ),
                "vertex": "1",
                "connectable": "0",
                "parent": f"node-{node['id']}",
            },
        )
        add_geometry(
            text_cell,
            x=text_x,
            y=text_y,
            width=text_width,
            height=text_height,
        )
        if node.get("badge"):
            badge_text = str(node["badge"])
            badge_width = max(46.0, min(82.0, 14.0 + 8.0 * len(badge_text)))
            badge = ET.SubElement(
                root,
                "mxCell",
                {
                    "id": f"badge-{node['id']}",
                    "value": badge_text,
                    "style": (
                        "rounded=1;arcSize=50;whiteSpace=wrap;html=1;"
                        f"fillColor={color};strokeColor={color};"
                        f"strokeWidth={supporting_stroke_px:.2f};"
                        f"fontColor=#FFFFFF;fontFamily={font_family};"
                        f"fontSize={fonts['badge']};"
                        "fontStyle=1;connectable=0;"
                    ),
                    "vertex": "1",
                    "connectable": "0",
                    "parent": f"node-{node['id']}",
                },
            )
            badge_height = max(24.0, fonts["badge"] * 1.6)
            add_geometry(
                badge,
                x=node["w"] - badge_width - 8.0,
                y=-badge_height * 0.54,
                width=badge_width,
                height=badge_height,
            )

    panel_label = spec.get("figure", {}).get("panel_label")
    if panel_label:
        cell = ET.SubElement(
            root,
            "mxCell",
            {
                "id": "panel-label",
                "value": str(panel_label),
                "style": (
                    "text;html=1;strokeColor=none;fillColor=none;"
                    "align=left;verticalAlign=middle;whiteSpace=wrap;"
                    f"fontColor={palette['ink']};fontFamily={font_family};"
                    f"fontSize={fonts['panel']};fontStyle=1;connectable=0;"
                ),
                "vertex": "1",
                "connectable": "0",
                "parent": "1",
                "data-panel-label": "1",
            },
        )
        add_geometry(cell, x=16, y=14, width=44, height=28)

    for index, annotation in enumerate(spec.get("annotations", []), start=1):
        tone = annotation.get("tone", "accent")
        color = palette[tone]
        text = str(annotation["text"])
        cell = ET.SubElement(
            root,
            "mxCell",
            {
                "id": f"annotation-{index}",
                "value": text,
                "style": (
                    "rounded=1;arcSize=50;whiteSpace=wrap;html=1;"
                    f"fillColor={blend(color, palette['canvas'], 0.93)};"
                    f"strokeColor={color};"
                    f"strokeWidth={supporting_stroke_px:.2f};"
                    f"fontColor={color};"
                    f"fontFamily={font_family};fontSize={fonts['annotation']};"
                    "fontStyle=1;connectable=0;"
                ),
                "vertex": "1",
                "connectable": "0",
                "parent": "1",
            },
        )
        annotation_width = float(
            annotation.get("w", max(90.0, min(190.0, 16.0 + 8.0 * len(text))))
        )
        annotation_height = float(
            annotation.get("h", max(28.0, fonts["annotation"] * 1.8))
        )
        add_geometry(
            cell,
            x=float(annotation["x"]),
            y=float(annotation["y"]),
            width=annotation_width,
            height=annotation_height,
        )

    icon_families = {item["family"] for item in icon_manifest}
    mxfile.set("data-icon-families", ",".join(sorted(icon_families)))
    mxfile.set("data-icon-family-count", str(len(icon_families)))
    return ET.ElementTree(mxfile), icon_manifest


def main() -> int:
    args = parse_args()
    spec_path = args.spec.resolve()
    out_path = args.out.resolve()
    if out_path.suffix.lower() != ".drawio":
        fail("--out must use the .drawio extension")
    skill_root = discover_paper_icons(args.paper_icons_skill)
    catalog = read_catalog(skill_root)
    academic_style = read_academic_style()
    spec = load_spec(spec_path)
    validate_spec(spec, catalog)
    paper_palette_path = resolve_paper_palette_path(
        spec,
        spec_path,
        args.paper_palette,
    )
    paper_palette = None
    paper_palette_digest = None
    if paper_palette_path is not None:
        paper_palette, paper_palette_digest = read_paper_palette(
            paper_palette_path,
            academic_style,
        )
    try:
        geometry, width, height, column, physical_width_mm = layout_nodes(
            spec,
            academic_style,
        )
        tree, manifest = build_figure(
            spec,
            geometry,
            width,
            height,
            column,
            physical_width_mm,
            skill_root,
            catalog,
            academic_style,
            paper_palette,
            paper_palette_digest,
        )
    except ValueError as exc:
        fail(f"cannot build figure: {exc}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(tree, space="  ")
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    manifest_path = (
        args.manifest.resolve()
        if args.manifest
        else out_path.with_name(out_path.stem + ".icons.json")
    )
    manifest_payload = {
        "figure": out_path.name,
        "spec": spec_path.name,
        "paper_icons_skill": skill_root.name,
        "path_policy": "portable basenames and paper-icons catalog URIs",
        "icon_family_policy": (
            "one coherent family unless the spec documents an exception"
        ),
        "paper_palette": (
            {
                "path": paper_palette_path.name,
                "palette_id": paper_palette["palette_id"],
                "schema_version": paper_palette["schema_version"],
                "status": paper_palette["status"],
                "sha256": paper_palette_digest,
            }
            if paper_palette is not None
            else None
        ),
        "icons": manifest,
    }
    manifest_path.write_text(
        json.dumps(manifest_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "drawio": str(out_path),
                "manifest": str(manifest_path),
                "nodes": len(spec["nodes"]),
                "edges": len(spec.get("edges", [])),
                "embedded_icons": len(manifest),
                "paper_icons_skill": str(skill_root),
                "paper_palette": (
                    paper_palette["palette_id"]
                    if paper_palette is not None
                    else None
                ),
                "paper_palette_sha256": paper_palette_digest,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
