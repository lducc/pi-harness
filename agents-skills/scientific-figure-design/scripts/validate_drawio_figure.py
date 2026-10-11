#!/usr/bin/env python3
"""Validate an icon-assisted draw.io figure for structure and paper readiness."""

from __future__ import annotations

import argparse
import colorsys
import hashlib
import json
import math
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree as ET

ACADEMIC_STYLE_PATH = (
    Path(__file__).resolve().parent.parent / "assets/academic-style.yaml"
)


def read_academic_style() -> dict:
    payload = json.loads(ACADEMIC_STYLE_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("academic style root must be an object")
    return payload


def normalize_hex(color: object) -> str:
    if not isinstance(color, str):
        raise ValueError(f"color must be a string, got {color!r}")
    raw = color.strip().lstrip("#")
    if len(raw) == 3:
        raw = "".join(character * 2 for character in raw)
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", raw):
        raise ValueError(f"invalid hex color {color!r}")
    return "#" + raw.upper()


def read_paper_palette(
    path: Path,
    academic_style: dict,
) -> tuple[dict, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("paper palette root must be an object")
    expected_schema = int(
        academic_style["color"]["paper_palette_schema_version"]
    )
    if payload.get("schema_version") != expected_schema:
        raise ValueError(
            f"schema_version must be {expected_schema}"
        )
    palette_id = payload.get("palette_id")
    if not isinstance(palette_id, str) or not palette_id.strip():
        raise ValueError("palette_id requires non-empty text")
    if payload.get("status", "draft") not in {"draft", "frozen"}:
        raise ValueError("status must be draft or frozen")
    if not isinstance(payload.get("paper_id", ""), str):
        raise ValueError("paper_id must be text")
    semantic = payload.get("semantic")
    if not isinstance(semantic, dict):
        raise TypeError("semantic must be an object")
    required_roles = set(academic_style["color"]["palette"])
    missing = sorted(required_roles - set(semantic))
    if missing:
        raise ValueError(
            "missing semantic roles: " + ", ".join(missing)
        )
    extra = sorted(set(semantic) - required_roles)
    if extra:
        raise ValueError(
            "unsupported semantic roles: " + ", ".join(extra)
        )
    normalized = dict(payload)
    normalized["semantic"] = {
        key: normalize_hex(value)
        for key, value in semantic.items()
    }
    chart_roles = payload.get("chart_roles", {})
    if not isinstance(chart_roles, dict):
        raise TypeError("chart_roles must be an object")
    normalized["chart_roles"] = {
        key: normalize_hex(value)
        for key, value in chart_roles.items()
    }
    unknown_chart_colors = sorted(
        set(normalized["chart_roles"].values())
        - set(normalized["semantic"].values())
    )
    if unknown_chart_colors:
        raise ValueError(
            "chart roles use colors outside semantic roles: "
            + ", ".join(unknown_chart_colors)
        )
    neutral_roles = {"canvas", "ink", "muted", "stroke", "neutral"}
    chromatic_colors = {
        value
        for role, value in normalized["semantic"].items()
        if role not in neutral_roles
    }
    maximum_hues = int(academic_style["color"]["maximum_semantic_hues"])
    if len(chromatic_colors) > maximum_hues:
        raise ValueError(
            f"paper palette uses {len(chromatic_colors)} semantic hues; "
            f"maximum is {maximum_hues}"
        )
    rules = payload.get("rules")
    if not isinstance(rules, dict):
        raise TypeError("rules must be an object")
    if rules.get("maximum_semantic_hues") != maximum_hues:
        raise ValueError(
            f"rules.maximum_semantic_hues must be {maximum_hues}"
        )
    canonical = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return normalized, hashlib.sha256(canonical).hexdigest()


def parse_style(raw: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for part in raw.split(";"):
        if "=" in part:
            key, value = part.split("=", 1)
            result[key] = value
    return result


def parse_number(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def parse_inline_css(raw: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for declaration in raw.split(";"):
        if ":" not in declaration:
            continue
        key, value = declaration.split(":", 1)
        result[key.strip().casefold()] = value.strip()
    return result


class HTMLTextStyleParser(HTMLParser):
    """Collect inline text styling that can alter legibility."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.colors: list[str] = []
        self.hidden_reasons: list[str] = []
        self.opacity_values: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = {
            key.casefold(): value or ""
            for key, value in attrs
        }
        if "hidden" in attributes:
            self.hidden_reasons.append("hidden attribute")
        if tag.casefold() == "font" and attributes.get("color"):
            self.colors.append(attributes["color"])
        css = parse_inline_css(attributes.get("style", ""))
        if css.get("color"):
            self.colors.append(css["color"])
        display = css.get("display", "").replace(" ", "").casefold()
        if display == "none":
            self.hidden_reasons.append("display:none")
        visibility = css.get("visibility", "").casefold()
        if visibility in {"hidden", "collapse"}:
            self.hidden_reasons.append(f"visibility:{visibility}")
        if "opacity" in css:
            self.opacity_values.append(css["opacity"])


def contrast_ratio(foreground: str, background: str) -> float:
    def luminance(color: str) -> float:
        channels = [
            int(color[index : index + 2], 16) / 255
            for index in (1, 3, 5)
        ]
        linear = [
            channel / 12.92
            if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return (
            0.2126 * linear[0]
            + 0.7152 * linear[1]
            + 0.0722 * linear[2]
        )

    first = luminance(foreground)
    second = luminance(background)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def validate(
    path: Path,
    manifest_path: Path | None = None,
    paper_palette_path: Path | None = None,
) -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warnings: list[str] = []
    summary: dict = {}
    try:
        academic_style = read_academic_style()
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        return [f"cannot read academic style {ACADEMIC_STYLE_PATH}: {exc}"], [], {}
    minimum_text_pt = float(
        academic_style["typography"]["minimum_final_text_pt"]
    )
    minimum_panel_label_pt = float(
        academic_style["typography"]["minimum_panel_label_pt"]
    )
    minimum_contrast_ratio = float(
        academic_style["typography"]["minimum_text_contrast_ratio"]
    )
    maximum_type_sizes = int(
        academic_style["typography"]["maximum_visible_type_sizes"]
    )
    maximum_icon_families = int(
        academic_style["icons"]["maximum_families"]
    )
    maximum_semantic_hues = int(
        academic_style["color"]["maximum_semantic_hues"]
    )
    primary_families = {
        family.casefold()
        for family in academic_style["typography"]["allowed_families"]
    }
    monospace_families = {
        family.casefold()
        for family in academic_style["typography"]["monospace_families"]
    }
    allowed_font_families = primary_families | monospace_families
    minimum_stroke_pt = float(
        academic_style["stroke"]["minimum_supporting_pt"]
    )
    maximum_stroke_pt = float(
        academic_style["stroke"]["maximum_emphasis_pt"]
    )
    icon_fraction_min, icon_fraction_max = (
        float(value)
        for value in academic_style["icons"]["size_fraction_of_node_height"]
    )
    maximum_icons_per_node = int(
        academic_style["icons"]["maximum_per_node"]
    )
    expected_style_version = str(academic_style.get("version", 1))
    paper_palette = None
    paper_palette_digest = None
    if paper_palette_path is not None:
        try:
            paper_palette, paper_palette_digest = read_paper_palette(
                paper_palette_path,
                academic_style,
            )
        except (
            OSError,
            json.JSONDecodeError,
            TypeError,
            ValueError,
        ) as exc:
            return [
                f"cannot read paper palette {paper_palette_path}: {exc}"
            ], [], {}
    try:
        tree = ET.parse(path)
    except (OSError, ET.ParseError) as exc:
        return [f"cannot parse draw.io XML: {exc}"], [], {}
    mxfile = tree.getroot()
    if mxfile.tag != "mxfile":
        errors.append("root element must be <mxfile>")
    for field in ("data-title", "data-description", "data-claim"):
        if not mxfile.get(field):
            errors.append(f"mxfile is missing {field} metadata")
    column = mxfile.get("data-column")
    if column not in {"single", "double"}:
        errors.append("mxfile data-column must be single or double")
    width_mm = parse_number(mxfile.get("data-width-mm"))
    if width_mm is None or width_mm <= 0:
        errors.append("mxfile data-width-mm must be a positive number")
        width_mm = None
    elif column in {"single", "double"}:
        width_key = f"{column}_column_width_mm"
        range_key = f"{column}_column_range_mm"
        expected_width = float(academic_style["geometry"][width_key])
        minimum_width, maximum_width = (
            float(value) for value in academic_style["geometry"][range_key]
        )
        if not minimum_width <= width_mm <= maximum_width:
            warnings.append(
                f"data-width-mm is {width_mm:g}; expected about "
                f"{expected_width:g} for {column} column "
                f"({minimum_width:g}–{maximum_width:g} mm allowed)"
            )
    if mxfile.get("data-academic-style-version") != expected_style_version:
        errors.append(
            "mxfile data-academic-style-version does not match "
            f"assets/academic-style.yaml version {expected_style_version}"
        )
    metadata_minimum_text_pt = parse_number(
        mxfile.get("data-minimum-text-pt")
    )
    if metadata_minimum_text_pt is None:
        errors.append("mxfile is missing valid data-minimum-text-pt metadata")
    elif abs(metadata_minimum_text_pt - minimum_text_pt) > 0.01:
        errors.append(
            "mxfile data-minimum-text-pt does not match the academic style"
        )
    semantic_colors_raw = mxfile.get("data-semantic-colors")
    if semantic_colors_raw is None:
        errors.append("mxfile is missing data-semantic-colors metadata")
        semantic_colors: set[str] = set()
    else:
        semantic_colors = {
            color.strip().upper()
            for color in semantic_colors_raw.split(",")
            if color.strip()
        }
        invalid_semantic_colors = sorted(
            color
            for color in semantic_colors
            if not re.fullmatch(r"#[0-9A-F]{6}", color)
        )
        if invalid_semantic_colors:
            errors.append(
                "invalid semantic color metadata: "
                + ", ".join(invalid_semantic_colors)
            )
    semantic_count = mxfile.get("data-semantic-color-count")
    try:
        declared_semantic_count = int(semantic_count or "")
    except ValueError:
        errors.append("mxfile has invalid data-semantic-color-count metadata")
    else:
        if declared_semantic_count != len(semantic_colors):
            errors.append(
                "data-semantic-color-count does not match "
                "data-semantic-colors"
            )
    if len(semantic_colors) > maximum_semantic_hues:
        warnings.append(
            f"figure declares {len(semantic_colors)} semantic hues; "
            f"maximum is {maximum_semantic_hues}"
        )
    palette_bound = mxfile.get("data-paper-palette-bound") == "1"
    source_palette_id = mxfile.get("data-paper-palette-id", "")
    source_palette_digest = mxfile.get("data-paper-palette-sha256", "")
    source_palette_schema = mxfile.get("data-paper-palette-schema", "")
    source_palette_status = mxfile.get("data-paper-palette-status", "")
    palette_metadata_present = any(
        (
            source_palette_id,
            source_palette_digest,
            source_palette_schema,
            source_palette_status,
        )
    )
    if palette_bound or palette_metadata_present:
        if not palette_bound:
            errors.append(
                "paper palette metadata exists but "
                "data-paper-palette-bound is not 1"
            )
        if not source_palette_id:
            errors.append("mxfile is missing data-paper-palette-id")
        if not re.fullmatch(r"[0-9a-f]{64}", source_palette_digest):
            errors.append(
                "mxfile data-paper-palette-sha256 must be lowercase SHA-256"
            )
        expected_palette_schema = str(
            academic_style["color"]["paper_palette_schema_version"]
        )
        if source_palette_schema != expected_palette_schema:
            errors.append(
                "mxfile data-paper-palette-schema does not match "
                f"academic policy version {expected_palette_schema}"
            )
        if source_palette_status not in {"draft", "frozen"}:
            errors.append(
                "mxfile data-paper-palette-status must be draft or frozen"
            )
        if paper_palette is None:
            warnings.append(
                "figure is bound to a paper palette but it was not verified; "
                "pass --paper-palette"
            )
    elif paper_palette is not None:
        errors.append(
            "a paper palette was supplied but the figure is not bound to one"
        )

    paper_palette_verified = False
    if palette_bound and paper_palette is not None:
        if source_palette_id != paper_palette["palette_id"]:
            errors.append(
                "figure paper palette ID does not match the supplied contract"
            )
        if source_palette_digest != paper_palette_digest:
            errors.append(
                "figure paper palette SHA-256 does not match the supplied "
                "contract"
            )
        if source_palette_status != paper_palette["status"]:
            errors.append(
                "figure paper palette status does not match the supplied "
                "contract"
            )
        expected_paper_id = paper_palette.get("paper_id", "")
        if expected_paper_id and mxfile.get("data-paper-id") != expected_paper_id:
            errors.append(
                "figure data-paper-id does not match the supplied contract"
            )
        nonsemantic_roles = {"canvas", "ink", "muted", "stroke", "neutral"}
        allowed_semantic_colors = {
            value
            for role, value in paper_palette["semantic"].items()
            if role not in nonsemantic_roles
        }
        drift = sorted(semantic_colors - allowed_semantic_colors)
        if drift:
            errors.append(
                "figure semantic colors drift from the supplied paper "
                "palette: " + ", ".join(drift)
            )
        paper_palette_verified = not any(
            "paper palette" in error
            or "data-paper-id" in error
            or "semantic colors drift" in error
            for error in errors
        )

    diagram = mxfile.find("diagram")
    if diagram is None:
        errors.append("diagram element is missing")
        return errors, warnings, summary
    model = diagram.find("mxGraphModel")
    if model is None:
        errors.append("mxGraphModel is missing")
        return errors, warnings, summary
    page_width = parse_number(model.get("pageWidth"))
    page_height = parse_number(model.get("pageHeight"))
    if not page_width or not page_height or page_width <= 0 or page_height <= 0:
        errors.append("pageWidth and pageHeight must be positive")
    if model.get("shadow", "0").casefold() not in {
        "0",
        "false",
        "none",
        "",
    }:
        warnings.append("mxGraphModel enables prohibited global shadows")
    expected_canvas = str(
        academic_style["color"]["palette"]["canvas"]
    ).upper()
    model_background = model.get("background", "")
    if model_background.upper() != expected_canvas:
        warnings.append(
            f"mxGraphModel background must be {expected_canvas}, "
            f"got {model_background or 'default'}"
        )

    root = model.find("root")
    if root is None:
        errors.append("mxGraphModel/root is missing")
        return errors, warnings, summary
    cells = root.findall("mxCell")
    ids = [cell.get("id") for cell in cells]
    duplicate_ids = [
        cell_id
        for cell_id, count in Counter(ids).items()
        if cell_id and count > 1
    ]
    if duplicate_ids:
        errors.append("duplicate mxCell ids: " + ", ".join(duplicate_ids[:10]))
    by_id = {cell.get("id"): cell for cell in cells if cell.get("id")}
    if "0" not in by_id or "1" not in by_id:
        errors.append("required root cells id=0 and id=1 are missing")

    vertices = [cell for cell in cells if cell.get("vertex") == "1"]
    edges = [cell for cell in cells if cell.get("edge") == "1"]
    nodes = [cell for cell in vertices if cell.get("data-node") == "1"]
    semantic_node_ids = {
        cell.get("id") for cell in nodes if cell.get("id")
    }
    icons = [cell for cell in vertices if cell.get("data-icon-id")]
    groups = [cell for cell in vertices if cell.get("data-group") == "1"]
    canvas_boundaries = [
        cell
        for cell in vertices
        if cell.get("data-canvas-boundary") == "1"
    ]
    summary.update(
        {
            "vertices": len(vertices),
            "nodes": len(nodes),
            "edges": len(edges),
            "groups": len(groups),
            "canvas_boundaries": len(canvas_boundaries),
            "embedded_icons": len(icons),
        }
    )
    if not nodes:
        warnings.append("no semantic nodes marked with data-node=1")

    connected: Counter[str] = Counter()
    for edge in edges:
        relation = edge.get("data-relation")
        if relation is None or not relation.strip():
            errors.append(
                f"edge {edge.get('id')!r} requires non-empty data-relation"
            )
        geometry = edge.find("mxGeometry")
        if geometry is None or geometry.get("relative") != "1":
            errors.append(
                f"edge {edge.get('id')!r} requires relative mxGeometry"
            )
        source, target = edge.get("source"), edge.get("target")
        if not source or source not in semantic_node_ids:
            errors.append(
                f"edge {edge.get('id')!r} source must be a semantic node"
            )
        else:
            connected[source] += 1
        if not target or target not in semantic_node_ids:
            errors.append(
                f"edge {edge.get('id')!r} target must be a semantic node"
            )
        else:
            connected[target] += 1
        style = parse_style(edge.get("style", ""))
        for required in ("rounded", "orthogonalLoop", "jettySize"):
            if required not in style:
                warnings.append(
                    f"edge {edge.get('id')!r} lacks routing property {required}"
                )

    if len(nodes) > 1:
        for node in nodes:
            if connected[node.get("id", "")] == 0:
                warnings.append(f"node {node.get('id')!r} is disconnected")

    icon_families: set[str] = set()
    embedded_icon_ids: Counter[str] = Counter()
    embedded_payloads: Counter[tuple[str, str, str]] = Counter()
    for icon in icons:
        icon_id = icon.get("data-icon-id", "")
        embedded_icon_ids[icon_id] += 1
        family = icon.get("data-icon-family", "")
        if not family:
            errors.append(
                f"icon {icon.get('id')!r} lacks data-icon-family metadata"
            )
        else:
            icon_families.add(family)
        if icon.get("parent") not in semantic_node_ids:
            errors.append(
                f"icon {icon.get('id')!r} must be a child of a semantic node"
            )
        else:
            parent_node = by_id.get(icon.get("parent", ""))
            if (
                parent_node is not None
                and parent_node.get("data-icon", "") != icon_id
            ):
                errors.append(
                    f"icon {icon.get('id')!r} does not match its parent "
                    "data-icon metadata"
                )
        style = parse_style(icon.get("style", ""))
        image = style.get("image", "")
        if not image.startswith("data:image/svg+xml,"):
            errors.append(
                f"icon {icon.get('id')!r} is not an embedded SVG data URI"
            )
        else:
            payload = unquote(image.split(",", 1)[1])
            payload_sha256 = hashlib.sha256(
                payload.encode("utf-8")
            ).hexdigest()
            embedded_payloads[
                (
                    icon.get("parent", "").removeprefix("node-"),
                    icon_id,
                    payload_sha256,
                )
            ] += 1
            try:
                svg_root = ET.fromstring(payload)
            except ET.ParseError as exc:
                errors.append(
                    f"icon {icon.get('id')!r} contains invalid SVG: {exc}"
                )
            else:
                if svg_root.tag.rsplit("}", 1)[-1].lower() != "svg":
                    errors.append(
                        f"icon {icon.get('id')!r} payload root is not <svg>"
                    )
                for element in svg_root.iter():
                    tag = element.tag.rsplit("}", 1)[-1].lower()
                    if tag in {
                        "script",
                        "style",
                        "image",
                        "foreignobject",
                        "lineargradient",
                        "radialgradient",
                        "filter",
                    }:
                        errors.append(
                            f"icon {icon.get('id')!r} contains prohibited "
                            f"<{tag}> content"
                        )
                    for attribute, value in element.attrib.items():
                        if (
                            attribute.rsplit("}", 1)[-1] == "href"
                            and value
                            and not value.startswith(("#", "data:"))
                        ):
                            errors.append(
                                f"icon {icon.get('id')!r} contains an external href"
                            )
                        for target in re.findall(
                            r"url\s*\(\s*[\"']?([^\"')]+)",
                            value,
                            flags=re.IGNORECASE,
                        ):
                            if not target.startswith(("#", "data:")):
                                errors.append(
                                    f"icon {icon.get('id')!r} contains "
                                    "an external CSS URL"
                                )

    for vertex in vertices:
        style = parse_style(vertex.get("style", ""))
        if (
            style.get("shape", "").casefold() == "image"
            and not vertex.get("data-icon-id")
        ):
            warnings.append(
                f"vertex {vertex.get('id')!r} is an untracked image cell"
            )

    if len(icon_families) > maximum_icon_families:
        warnings.append(
            "multiple icon families are present: " + ", ".join(sorted(icon_families))
        )
    icon_family_metadata = {
        family
        for family in mxfile.get("data-icon-families", "").split(",")
        if family
    }
    if icon_family_metadata != icon_families:
        errors.append(
            "data-icon-families metadata does not match embedded icons"
        )
    try:
        declared_icon_family_count = int(
            mxfile.get("data-icon-family-count", "")
        )
    except ValueError:
        errors.append("mxfile has invalid data-icon-family-count metadata")
    else:
        if declared_icon_family_count != len(icon_families):
            errors.append(
                "data-icon-family-count does not match embedded icons"
            )

    icon_parent_counts = Counter(icon.get("parent") for icon in icons)
    for parent, count in icon_parent_counts.items():
        if count > maximum_icons_per_node:
            warnings.append(
                f"node {parent!r} contains {count} icons; "
                f"maximum is {maximum_icons_per_node}"
            )
    resolved_manifest = manifest_path or path.with_name(
        path.stem + ".icons.json"
    )
    if icons:
        try:
            manifest_payload = json.loads(
                resolved_manifest.read_text(encoding="utf-8")
            )
            manifest_icons = manifest_payload["icons"]
            if not isinstance(manifest_icons, list):
                raise TypeError("icons must be a list")
            if not all(isinstance(item, dict) for item in manifest_icons):
                raise TypeError("every icon entry must be an object")
            manifest_icon_ids: Counter[str] = Counter()
            manifest_node_icons: Counter[tuple[str, str]] = Counter()
            manifest_payloads: Counter[tuple[str, str, str]] = Counter()
            manifest_families: set[str] = set()
            for index, item in enumerate(manifest_icons):
                for field in (
                    "node_id",
                    "icon_id",
                    "family",
                    "source",
                    "source_svg",
                    "catalog_svg",
                    "payload_sha256",
                ):
                    if not item.get(field):
                        raise TypeError(
                            f"icon entry {index} is missing {field}"
                        )
                if item.get("embedded") is not True:
                    raise TypeError(
                        f"icon entry {index} must declare embedded=true"
                    )
                manifest_icon_ids[str(item["icon_id"])] += 1
                manifest_node_icons[
                    (str(item["node_id"]), str(item["icon_id"]))
                ] += 1
                payload_sha256 = str(item["payload_sha256"])
                if not re.fullmatch(r"[0-9a-f]{64}", payload_sha256):
                    raise TypeError(
                        f"icon entry {index} has invalid payload_sha256"
                    )
                manifest_payloads[
                    (
                        str(item["node_id"]),
                        str(item["icon_id"]),
                        payload_sha256,
                    )
                ] += 1
                manifest_family = str(item["family"])
                manifest_families.add(manifest_family)
                catalog_parts = (
                    str(item["catalog_svg"])
                    .replace("\\", "/")
                    .casefold()
                    .split("/")
                )
                path_families = {
                    "lucide",
                    "tabler",
                    "phosphor",
                    "duotone",
                    "brand",
                    "fetched",
                }
                path_family = next(
                    (
                        part
                        for part in catalog_parts
                        if part in path_families
                    ),
                    "original",
                )
                if path_family == "fetched":
                    path_family = "lucide"
                if manifest_family != path_family:
                    raise TypeError(
                        f"icon entry {index} family does not match catalog_svg"
                    )
        except (
            OSError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
        ) as exc:
            errors.append(
                f"cannot read icon source manifest {resolved_manifest}: {exc}"
            )
        else:
            if manifest_icon_ids != embedded_icon_ids:
                errors.append(
                    "icon source manifest does not match embedded icons"
                )
            embedded_node_icons = Counter(
                (
                    icon.get("parent", "").removeprefix("node-"),
                    icon.get("data-icon-id", ""),
                )
                for icon in icons
            )
            if manifest_node_icons != embedded_node_icons:
                errors.append(
                    "icon source manifest node assignments do not match "
                    "embedded icons"
                )
            if manifest_payloads != embedded_payloads:
                errors.append(
                    "icon source manifest payload SHA-256 values do not "
                    "match embedded SVG payloads"
                )
            if manifest_families != icon_families:
                errors.append(
                    "icon source manifest families do not match embedded icons"
                )

    local_boxes: dict[str, tuple[float, float, float, float]] = {}
    for cell in vertices:
        geometry = cell.find("mxGeometry")
        if geometry is None:
            errors.append(f"vertex {cell.get('id')!r} has no mxGeometry")
            continue
        values = [
            parse_number(geometry.get("x", "0")),
            parse_number(geometry.get("y", "0")),
            parse_number(geometry.get("width")),
            parse_number(geometry.get("height")),
        ]
        if any(value is None for value in values):
            errors.append(f"vertex {cell.get('id')!r} has invalid geometry")
            continue
        x, y, width, height = (float(value) for value in values)
        if width <= 0 or height <= 0:
            errors.append(f"vertex {cell.get('id')!r} has non-positive size")
        if cell.get("id"):
            local_boxes[cell.get("id", "")] = (x, y, width, height)
        if cell.get("parent") == "1":
            if x < 0 or y < 0:
                errors.append(f"vertex {cell.get('id')!r} is off-canvas")
            if page_width and page_height and (
                x + width > page_width + 1 or y + height > page_height + 1
            ):
                warnings.append(f"vertex {cell.get('id')!r} exceeds the page")

    if len(canvas_boundaries) != 1:
        errors.append(
            "draw.io source requires exactly one data-canvas-boundary=1 cell"
        )
    elif page_width and page_height:
        boundary_id = canvas_boundaries[0].get("id", "")
        boundary_box = local_boxes.get(boundary_id)
        if boundary_box is None:
            errors.append("canvas boundary has invalid geometry")
        else:
            x, y, boundary_width, boundary_height = boundary_box
            if (
                abs(x) > 0.1
                or abs(y) > 0.1
                or abs(boundary_width - page_width) > 0.1
                or abs(boundary_height - page_height) > 0.1
            ):
                errors.append(
                    "canvas boundary must exactly match pageWidth and pageHeight"
                )

    absolute_cache: dict[str, tuple[float, float]] = {}

    def absolute_xy(cell_id: str, trail: set[str] | None = None) -> tuple[float, float]:
        if cell_id in absolute_cache:
            return absolute_cache[cell_id]
        if trail is None:
            trail = set()
        if cell_id in trail:
            errors.append(f"parent cycle detected at {cell_id!r}")
            return 0.0, 0.0
        trail = {*trail, cell_id}
        cell = by_id[cell_id]
        x, y, _, _ = local_boxes.get(cell_id, (0.0, 0.0, 0.0, 0.0))
        parent = cell.get("parent")
        if parent and parent not in by_id:
            errors.append(
                f"vertex {cell_id!r} references missing parent {parent!r}"
            )
        if parent and parent not in {"0", "1"} and parent in by_id:
            parent_x, parent_y = absolute_xy(parent, trail)
            x += parent_x
            y += parent_y
        absolute_cache[cell_id] = (x, y)
        return x, y

    for vertex in vertices:
        vertex_id = vertex.get("id")
        if not vertex_id or vertex_id not in local_boxes:
            continue
        x, y = absolute_xy(vertex_id)
        _, _, vertex_width, vertex_height = local_boxes[vertex_id]
        if x < -1 or y < -1:
            errors.append(f"vertex {vertex_id!r} is off-canvas")
        if page_width and page_height and (
            x + vertex_width > page_width + 1
            or y + vertex_height > page_height + 1
        ):
            warnings.append(f"vertex {vertex_id!r} exceeds the page")

    semantic_boxes: list[tuple[str, float, float, float, float]] = []
    for node in nodes:
        node_id = node.get("id")
        if not node_id or node_id not in local_boxes:
            continue
        x, y = absolute_xy(node_id)
        _, _, width, height = local_boxes[node_id]
        semantic_boxes.append((node_id, x, y, width, height))
        if x < 0 or y < 0:
            errors.append(f"semantic node {node_id!r} is off-canvas")
        if page_width and page_height and (
            x + width > page_width + 1 or y + height > page_height + 1
        ):
            warnings.append(f"semantic node {node_id!r} exceeds the page")

    for index, first in enumerate(semantic_boxes):
        for second in semantic_boxes[index + 1 :]:
            _, ax, ay, aw, ah = first
            _, bx, by, bw, bh = second
            overlap_x = min(ax + aw, bx + bw) - max(ax, bx)
            overlap_y = min(ay + ah, by + bh) - max(ay, by)
            if overlap_x > 1 and overlap_y > 1:
                warnings.append(
                    f"semantic nodes {first[0]!r} and {second[0]!r} overlap"
                )

    for icon in icons:
        icon_id = icon.get("id")
        parent_id = icon.get("parent")
        if (
            not icon_id
            or icon_id not in local_boxes
            or not parent_id
            or parent_id not in local_boxes
        ):
            continue
        _, _, icon_width, icon_height = local_boxes[icon_id]
        _, _, _, parent_height = local_boxes[parent_id]
        if parent_height <= 0:
            continue
        width_fraction = icon_width / parent_height
        height_fraction = icon_height / parent_height
        if abs(icon_width - icon_height) > max(icon_width, icon_height) * 0.05:
            warnings.append(f"icon {icon_id!r} must remain approximately square")
        if not (
            icon_fraction_min - 0.01
            <= width_fraction
            <= icon_fraction_max + 0.01
            and icon_fraction_min - 0.01
            <= height_fraction
            <= icon_fraction_max + 0.01
        ):
            warnings.append(
                f"icon {icon_id!r} occupies "
                f"{width_fraction:.0%} × {height_fraction:.0%} of node height; "
                f"expected {icon_fraction_min:.0%}–{icon_fraction_max:.0%}"
            )

    visible_type_sizes: set[float] = set()
    visible_primary_families: set[str] = set()
    visible_monospace_families: set[str] = set()
    reported_opacity_issues: set[tuple[str, str, str]] = set()

    def is_code_cell(cell: ET.Element) -> bool:
        current: ET.Element | None = cell
        visited: set[str] = set()
        while current is not None:
            if (
                current.get("data-kind", "").casefold() == "code"
                or current.get("data-code") == "1"
            ):
                return True
            parent = current.get("parent")
            if not parent or parent in visited:
                return False
            visited.add(parent)
            current = by_id.get(parent)
        return False

    def effective_background(cell: ET.Element) -> str:
        current: ET.Element | None = cell
        visited: set[str] = set()
        while current is not None:
            current_style = parse_style(current.get("style", ""))
            for key in ("labelBackgroundColor", "fillColor"):
                candidate = current_style.get(key, "")
                if re.fullmatch(r"#[0-9A-Fa-f]{6}", candidate):
                    return candidate.upper()
            parent = current.get("parent")
            if not parent or parent in visited:
                break
            visited.add(parent)
            current = by_id.get(parent)
        return expected_canvas

    if width_mm and page_width:
        for cell in cells:
            cell_value = cell.get("value", "")
            if not cell_value:
                continue
            style = parse_style(cell.get("style", ""))
            opacity_source: ET.Element | None = cell
            visited_opacity_sources: set[str] = set()
            while opacity_source is not None:
                opacity_style = parse_style(opacity_source.get("style", ""))
                source_id = opacity_source.get("id", "")
                for opacity_key in ("textOpacity", "opacity"):
                    if opacity_key not in opacity_style:
                        continue
                    opacity_raw = opacity_style[opacity_key]
                    issue = (source_id, opacity_key, opacity_raw)
                    if issue in reported_opacity_issues:
                        continue
                    reported_opacity_issues.add(issue)
                    opacity = parse_number(opacity_raw)
                    scope = (
                        ""
                        if opacity_source is cell
                        else f" affecting text cell {cell.get('id')!r}"
                    )
                    if opacity is None:
                        errors.append(
                            f"cell {source_id!r} has invalid "
                            f"{opacity_key}={opacity_raw!r}{scope}"
                        )
                    elif abs(opacity - 100.0) > 0.01:
                        errors.append(
                            f"cell {source_id!r} uses {opacity_key}="
                            f"{opacity:g}{scope}; visible text requires 100"
                        )
                parent = opacity_source.get("parent")
                if not parent or parent in visited_opacity_sources:
                    break
                visited_opacity_sources.add(parent)
                opacity_source = by_id.get(parent)
            html_styles = HTMLTextStyleParser()
            try:
                html_styles.feed(cell_value)
                html_styles.close()
            except Exception as exc:
                errors.append(
                    f"cell {cell.get('id')!r} has malformed HTML text: {exc}"
                )
            for reason in sorted(set(html_styles.hidden_reasons)):
                errors.append(
                    f"cell {cell.get('id')!r} hides text with {reason}"
                )
            for css_opacity in html_styles.opacity_values:
                opacity = parse_number(css_opacity)
                if opacity is None:
                    errors.append(
                        f"cell {cell.get('id')!r} has invalid inline CSS "
                        f"opacity={css_opacity!r}"
                    )
                elif abs(opacity - 1.0) > 0.001:
                    errors.append(
                        f"cell {cell.get('id')!r} uses inline CSS opacity="
                        f"{opacity:g}; visible text requires 1"
                    )
            sizes: list[float] = []
            style_size = parse_number(style.get("fontSize"))
            if style_size:
                sizes.append(style_size)
            for amount, unit in re.findall(
                r"font-size\s*:\s*(\d+(?:\.\d+)?)\s*([A-Za-z%]*)",
                cell_value,
                flags=re.IGNORECASE,
            ):
                unit = unit.casefold() or "px"
                if unit == "px":
                    sizes.append(float(amount))
                elif unit == "pt":
                    sizes.append(float(amount) * 96.0 / 72.0)
                else:
                    warnings.append(
                        f"cell {cell.get('id')!r} uses unsupported "
                        f"font-size unit {unit!r}"
                    )
            if re.search(
                r"<font\b[^>]*\bsize\s*=",
                cell_value,
                flags=re.IGNORECASE,
            ):
                warnings.append(
                    f"cell {cell.get('id')!r} uses ambiguous HTML font size"
                )
            if not sizes:
                warnings.append(
                    f"cell {cell.get('id')!r} has no explicit font size"
                )
            for font_size in sorted(set(sizes)):
                final_points = font_size * width_mm / page_width / 25.4 * 72
                visible_type_sizes.add(round(final_points, 2))
                required_text_pt = (
                    minimum_panel_label_pt
                    if cell.get("data-panel-label") == "1"
                    else minimum_text_pt
                )
                if final_points < required_text_pt - 0.01:
                    warnings.append(
                        f"cell {cell.get('id')!r} uses {font_size:g}px text "
                        f"({final_points:.2f} pt) below "
                        f"{required_text_pt:g} pt at final width"
                    )
            family_declarations = []
            if style.get("fontFamily"):
                family_declarations.append(style["fontFamily"])
            family_declarations.extend(
                match[0] or match[1]
                for match in re.findall(
                    r"font-family\s*:\s*"
                    r"(?:[\"']([^\"']+)[\"']|([^;\"']+))",
                    cell_value,
                    flags=re.IGNORECASE,
                )
            )
            family_declarations.extend(
                re.findall(
                    r"<font\b[^>]*\bface\s*=\s*[\"']([^\"']+)[\"']",
                    cell_value,
                    flags=re.IGNORECASE,
                )
            )
            if not family_declarations:
                warnings.append(
                    f"cell {cell.get('id')!r} has no explicit font family"
                )
            for declaration in family_declarations:
                families = [
                    family.strip().strip("\"'").casefold()
                    for family in declaration.split(",")
                    if family.strip()
                ]
                unknown = [
                    family
                    for family in families
                    if family not in allowed_font_families
                ]
                if unknown:
                    warnings.append(
                        f"cell {cell.get('id')!r} uses disallowed font "
                        + ", ".join(unknown)
                    )
                if families:
                    first = families[0]
                    if first in monospace_families:
                        visible_monospace_families.add(first)
                        if not is_code_cell(cell):
                            warnings.append(
                                f"cell {cell.get('id')!r} uses monospace "
                                "outside code content"
                            )
                    else:
                        visible_primary_families.add(first)
            if re.search(
                r"[\U0001F300-\U0001FAFF\u2600-\u27BF]",
                re.sub(r"<[^>]+>", "", cell_value),
            ):
                warnings.append(
                    f"cell {cell.get('id')!r} contains prohibited emoji"
                )
            foregrounds: set[str] = set()
            if re.fullmatch(
                r"#[0-9A-Fa-f]{6}",
                style.get("fontColor", ""),
            ):
                foregrounds.add(style["fontColor"].upper())
            foregrounds.update(
                color.upper()
                for color in re.findall(
                    r"<font\b[^>]*\bcolor\s*=\s*[\"']"
                    r"(#[0-9A-Fa-f]{6})[\"']",
                    cell_value,
                    flags=re.IGNORECASE,
                )
            )
            for color in html_styles.colors:
                if re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
                    foregrounds.add(color.upper())
                elif color.casefold() in {"transparent", "none"} or re.fullmatch(
                    r"rgba\(\s*\d+(?:\.\d+)?\s*,\s*"
                    r"\d+(?:\.\d+)?\s*,\s*\d+(?:\.\d+)?\s*,\s*0(?:\.0+)?\s*\)",
                    color,
                    flags=re.IGNORECASE,
                ):
                    errors.append(
                        f"cell {cell.get('id')!r} hides text with "
                        f"color={color!r}"
                    )
                else:
                    warnings.append(
                        f"cell {cell.get('id')!r} uses non-canonical "
                        f"HTML text color {color!r}; require #RRGGBB"
                    )
            if not foregrounds:
                warnings.append(
                    f"cell {cell.get('id')!r} has no canonical fontColor"
                )
            background = effective_background(cell)
            for foreground in foregrounds:
                ratio = contrast_ratio(foreground, background)
                if ratio + 0.01 < minimum_contrast_ratio:
                    warnings.append(
                        f"cell {cell.get('id')!r} text contrast is "
                        f"{ratio:.2f}:1; minimum is "
                        f"{minimum_contrast_ratio:g}:1"
                    )

        if len(visible_type_sizes) > maximum_type_sizes:
            warnings.append(
                f"figure uses {len(visible_type_sizes)} visible type sizes; "
                f"maximum is {maximum_type_sizes}"
            )
        if len(visible_primary_families) > 1:
            warnings.append(
                "figure uses multiple primary font families: "
                + ", ".join(sorted(visible_primary_families))
            )
        if len(visible_monospace_families) > 1:
            warnings.append(
                "figure uses multiple monospace font families: "
                + ", ".join(sorted(visible_monospace_families))
            )

    prohibited_effect_keys = {
        "shadow": "shadow",
        "glass": "glass",
        "comic": "comic mode",
        "sketch": "sketch mode",
        "3d": "3D",
        "threeD": "3D",
        "flowAnimation": "connector animation",
    }
    style_colors: set[str] = set()
    for cell in cells:
        style = parse_style(cell.get("style", ""))
        shape = style.get("shape", "").casefold()
        if "cube" in shape or shape in {"3d", "isometric"}:
            warnings.append(
                f"cell {cell.get('id')!r} uses prohibited faux-3D shape "
                f"{shape!r}"
            )
        for color_key in (
            "fillColor",
            "strokeColor",
            "fontColor",
            "labelBackgroundColor",
            "gradientColor",
        ):
            color_value = style.get(color_key)
            if (
                color_value
                and color_value.casefold()
                not in {"none", "transparent", "default"}
                and not re.fullmatch(r"#[0-9A-Fa-f]{6}", color_value)
            ):
                warnings.append(
                    f"cell {cell.get('id')!r} uses non-canonical "
                    f"{color_key}={color_value!r}; require #RRGGBB"
                )
        gradient = style.get("gradientColor", "none")
        if gradient.casefold() not in {"none", "default", ""}:
            warnings.append(
                f"cell {cell.get('id')!r} uses a prohibited gradient"
            )
        for key, label in prohibited_effect_keys.items():
            if style.get(key, "0").casefold() not in {
                "0",
                "false",
                "none",
                "",
            }:
                warnings.append(
                    f"cell {cell.get('id')!r} uses prohibited {label}"
                )
        stroke_color = style.get("strokeColor", "")
        if (
            (cell.get("vertex") == "1" or cell.get("edge") == "1")
            and "strokeColor" not in style
        ):
            warnings.append(
                f"cell {cell.get('id')!r} has no explicit strokeColor"
            )
        if stroke_color.casefold() not in {"", "none", "transparent"}:
            if "strokeWidth" not in style:
                warnings.append(
                    f"cell {cell.get('id')!r} has no explicit strokeWidth"
                )
            stroke_width_raw = style.get("strokeWidth", "1")
            stroke_width = parse_number(stroke_width_raw)
            if stroke_width is None:
                errors.append(
                    f"cell {cell.get('id')!r} has invalid strokeWidth"
                )
            elif width_mm and page_width:
                final_stroke_pt = (
                    stroke_width * width_mm / page_width / 25.4 * 72
                )
                if final_stroke_pt < minimum_stroke_pt - 0.01:
                    warnings.append(
                        f"cell {cell.get('id')!r} uses "
                        f"{final_stroke_pt:.2f} pt stroke below "
                        f"{minimum_stroke_pt:g} pt"
                    )
                if final_stroke_pt > maximum_stroke_pt + 0.01:
                    warnings.append(
                        f"cell {cell.get('id')!r} uses "
                        f"{final_stroke_pt:.2f} pt stroke above "
                        f"{maximum_stroke_pt:g} pt"
                    )
        style_colors.update(
            color.upper()
            for color in re.findall(
                r"#[0-9A-Fa-f]{6}",
                cell.get("style", ""),
            )
        )

    active_palette = (
        paper_palette["semantic"]
        if paper_palette_verified
        else academic_style["color"]["palette"]
    )
    neutral_palette_colors = {
        str(active_palette[key]).upper()
        for key in ("canvas", "ink", "muted", "stroke", "neutral")
    }

    def color_hls(color: str) -> tuple[float, float, float]:
        red, green, blue = (
            int(color[index : index + 2], 16) / 255
            for index in (1, 3, 5)
        )
        return colorsys.rgb_to_hls(red, green, blue)

    declared_hues = [
        color_hls(color)[0]
        for color in semantic_colors | neutral_palette_colors
        if color_hls(color)[2] >= 0.05
    ]

    def hue_distance(first: float, second: float) -> float:
        difference = abs(first - second)
        return min(difference, 1.0 - difference)

    undeclared_accents = sorted(
        color
        for color in style_colors
        if color not in neutral_palette_colors
        and color not in semantic_colors
        and color_hls(color)[2] >= 0.16
        and not any(
            hue_distance(color_hls(color)[0], hue) <= 0.06
            for hue in declared_hues
        )
    )
    if undeclared_accents:
        warnings.append(
            "figure uses undeclared accent colors: "
            + ", ".join(undeclared_accents)
        )
    summary.update(
        {
            "column": column,
            "width_mm": width_mm,
            "academic_style_version": expected_style_version,
            "minimum_text_pt": minimum_text_pt,
            "visible_type_sizes_pt": sorted(visible_type_sizes),
            "primary_font_families": sorted(visible_primary_families),
            "icon_families": sorted(icon_families),
            "semantic_colors": sorted(semantic_colors),
            "paper_palette_id": source_palette_id or None,
            "paper_palette_sha256": source_palette_digest or None,
            "paper_palette_status": source_palette_status or None,
            "paper_palette_verified": paper_palette_verified,
        }
    )
    return errors, warnings, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("figure", type=Path)
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Icon/source manifest; defaults to FIGURE.icons.json.",
    )
    parser.add_argument(
        "--paper-palette",
        type=Path,
        help="Paper-level palette contract used to build the figure.",
    )
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    errors, warnings, summary = validate(
        args.figure.resolve(),
        args.manifest.resolve() if args.manifest else None,
        args.paper_palette.resolve() if args.paper_palette else None,
    )
    if args.as_json:
        print(
            json.dumps(
                {"errors": errors, "warnings": warnings, "summary": summary},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for error in errors:
            print(f"ERROR: {error}")
        for warning in warnings:
            print(f"WARNING: {warning}")
        print(
            f"{args.figure}: {len(errors)} error(s), {len(warnings)} warning(s)"
        )
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
