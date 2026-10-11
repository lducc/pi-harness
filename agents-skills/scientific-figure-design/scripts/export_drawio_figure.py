#!/usr/bin/env python3
"""Export an editable draw.io paper figure to preview and publication formats."""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import shutil
import struct
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_IEND = b"\x00\x00\x00\x00IEND\xaeB`\x82"
ACADEMIC_STYLE_PATH = (
    Path(__file__).resolve().parent.parent / "assets/academic-style.yaml"
)


def academic_style() -> dict:
    try:
        payload = json.loads(
            ACADEMIC_STYLE_PATH.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(
            f"cannot read academic style {ACADEMIC_STYLE_PATH}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise SystemExit("academic style root must be an object")
    return payload


def detect_drawio(explicit: str | None) -> str:
    candidates = [
        explicit,
        shutil.which("drawio"),
        shutil.which("draw.io"),
        "/Applications/draw.io.app/Contents/MacOS/draw.io",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if path.is_file() and path.stat().st_mode & 0o111:
            return str(path.resolve())
    raise SystemExit(
        "draw.io CLI was not found. Install draw.io desktop or pass --drawio-bin."
    )


def metadata(drawio_path: Path) -> dict[str, str]:
    try:
        root = ET.parse(drawio_path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise SystemExit(f"cannot read draw.io metadata: {exc}")
    width_raw = root.get("data-width-mm")
    try:
        width_mm = float(width_raw or "")
    except ValueError as exc:
        raise SystemExit(
            "draw.io source has invalid data-width-mm metadata"
        ) from exc
    if width_mm <= 0:
        raise SystemExit("draw.io source data-width-mm must be positive")
    model = root.find("diagram/mxGraphModel")
    if model is None:
        raise SystemExit("draw.io source has no mxGraphModel")
    try:
        page_width = float(model.get("pageWidth", ""))
        page_height = float(model.get("pageHeight", ""))
    except ValueError as exc:
        raise SystemExit("draw.io source has invalid page geometry") from exc
    if page_width <= 0 or page_height <= 0:
        raise SystemExit("draw.io source page geometry must be positive")
    return {
        "title": root.get("data-title", drawio_path.stem),
        "description": root.get("data-description", ""),
        "claim": root.get("data-claim", ""),
        "width_mm": f"{width_mm:g}",
        "academic_style_version": root.get(
            "data-academic-style-version",
            "",
        ),
        "page_width": f"{page_width:g}",
        "page_height": f"{page_height:g}",
    }


def run(command: list[str], timeout: int = 120) -> None:
    try:
        result = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(
            f"draw.io export timed out after {timeout}s.\nCommand: "
            + " ".join(command)
        ) from exc
    except OSError as exc:
        raise SystemExit(f"cannot execute draw.io CLI: {exc}") from exc
    if result.returncode != 0:
        raise SystemExit(
            "draw.io export failed.\nCommand: "
            + " ".join(command)
            + "\nOutput:\n"
            + result.stdout
        )


def repair_png(path: Path) -> str:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise SystemExit(f"{path} is not a PNG file")
    if data.endswith(PNG_IEND):
        return "already-complete"
    if data.endswith(b"\x00\x00\x00\x00"):
        path.write_bytes(data + b"IEND\xaeB`\x82")
        return "repaired"
    raise SystemExit(f"{path} has an unexpected PNG ending; refusing to modify it")


def validate_png_dpi(path: Path, width_mm: float, minimum_dpi: int) -> float:
    data = path.read_bytes()
    if len(data) < 24 or not data.startswith(PNG_SIGNATURE):
        raise SystemExit(f"{path} is not a complete PNG file")
    pixel_width, _ = struct.unpack(">II", data[16:24])
    actual_dpi = pixel_width / (width_mm / 25.4)
    if actual_dpi + 0.5 < minimum_dpi:
        raise SystemExit(
            f"{path} is {actual_dpi:.1f} dpi at {width_mm:g} mm; "
            f"minimum is {minimum_dpi} dpi"
        )
    return actual_dpi


def normalize_pdf_size(
    path: Path,
    info: dict[str, str],
    timeout: int,
) -> str:
    ghostscript = shutil.which("gs")
    if not ghostscript:
        raise SystemExit(
            "final PDF export requires Ghostscript to normalize the page to "
            "the declared physical width; install Ghostscript or request SVG "
            "as the vector master"
        )
    target_width_pt = float(info["width_mm"]) / 25.4 * 72.0
    target_height_pt = (
        target_width_pt
        * float(info["page_height"])
        / float(info["page_width"])
    )
    normalized = path.with_name(path.stem + ".physical.pdf")
    command = [
        ghostscript,
        "-q",
        "-dNOPAUSE",
        "-dBATCH",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.7",
        f"-dDEVICEWIDTHPOINTS={target_width_pt:.3f}",
        f"-dDEVICEHEIGHTPOINTS={target_height_pt:.3f}",
        "-dFIXEDMEDIA",
        "-dPDFFitPage",
        "-dAutoRotatePages=/None",
        f"-sOutputFile={normalized}",
        str(path),
    ]
    run(command, timeout)
    normalized.replace(path)
    return (
        f"normalized to {target_width_pt:.2f} × "
        f"{target_height_pt:.2f} pt"
    )


def polish_svg(path: Path, info: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    root_match = re.search(r"<svg\b([^>]*)>", text, re.IGNORECASE | re.DOTALL)
    if not root_match:
        raise SystemExit(f"exported SVG has no root element: {path}")
    attributes = root_match.group(1)
    viewbox_match = re.search(
        r'viewBox\s*=\s*["\']([^"\']+)["\']', attributes, re.IGNORECASE
    )
    width_mm = float(info["width_mm"])
    height_mm = None
    if viewbox_match:
        try:
            values = [float(value) for value in viewbox_match.group(1).split()]
        except ValueError as exc:
            raise SystemExit(f"exported SVG has an invalid viewBox: {path}") from exc
        if len(values) == 4 and values[2] > 0:
            page_width = float(info["page_width"])
            if abs(values[2] - page_width) / page_width > 0.01:
                raise SystemExit(
                    "exported SVG viewBox does not match the academic canvas "
                    f"width ({values[2]:g} vs {page_width:g}). Keep the "
                    "canvas boundary and export final artifacts with border 0."
                )
            height_mm = width_mm * values[3] / values[2]
    new_attributes = re.sub(
        r'\swidth\s*=\s*["\'][^"\']*["\']',
        "",
        attributes,
        flags=re.IGNORECASE,
    )
    new_attributes = re.sub(
        r'\sheight\s*=\s*["\'][^"\']*["\']',
        "",
        new_attributes,
        flags=re.IGNORECASE,
    )
    if not re.search(r"\sfont-family\s*=", new_attributes, re.IGNORECASE):
        new_attributes += ' font-family="Arial, Helvetica, sans-serif"'
    dimensions = f' width="{width_mm:.1f}mm"'
    if height_mm:
        dimensions += f' height="{height_mm:.1f}mm"'
    new_root = f"<svg{new_attributes}{dimensions}>"
    title = html.escape(info["title"])
    description = html.escape(
        " ".join(part for part in (info["description"], info["claim"]) if part)
    )
    accessible = f"<title>{title}</title><desc>{description}</desc>"
    text = (
        text[: root_match.start()]
        + new_root
        + accessible
        + text[root_match.end() :]
    )
    text = re.sub(
        r'<switch><g requiredFeatures="http://www\.w3\.org/TR/SVG11/'
        r'feature#Extensibility"\s*/><a[^>]+xlink:href="https://www\.drawio\.com/'
        r'doc/faq/svg-export-text-problems"[^>]*><text[^>]*>'
        r'Text is not SVG - cannot display</text></a></switch>(?=</svg>)',
        "",
        text,
        flags=re.IGNORECASE,
    )
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("figure", type=Path)
    parser.add_argument(
        "--mode",
        choices=["preview", "final", "all"],
        default="preview",
    )
    parser.add_argument(
        "--formats",
        default="svg,pdf,png",
        help="Comma-separated final formats: svg,pdf,png,jpg.",
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--name")
    parser.add_argument("--drawio-bin")
    parser.add_argument("--scale", type=float, default=2.0)
    parser.add_argument("--border", type=int, default=0)
    parser.add_argument(
        "--dpi",
        type=int,
        help="Final PNG/JPG target DPI; defaults to academic-style.yaml.",
    )
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    if args.mode in {"final", "all"} and args.border != 0:
        raise SystemExit(
            "final academic exports require --border 0; keep whitespace "
            "inside the canvas instead"
        )

    figure = args.figure.resolve()
    if not figure.is_file():
        raise SystemExit(f"draw.io source does not exist: {figure}")
    drawio = detect_drawio(args.drawio_bin)
    out_dir = (
        args.output_dir.resolve() if args.output_dir else figure.parent.resolve()
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    name = args.name or figure.stem
    info = metadata(figure)
    policy = academic_style()
    expected_style_version = str(policy.get("version", 1))
    if info["academic_style_version"] != expected_style_version:
        raise SystemExit(
            "draw.io source academic style version does not match "
            f"assets/academic-style.yaml version {expected_style_version}; "
            "rebuild and validate before export"
        )
    minimum_dpi = int(policy["export"]["minimum_png_dpi"])
    target_dpi = args.dpi or minimum_dpi
    if target_dpi < minimum_dpi:
        raise SystemExit(
            f"--dpi must be at least the academic minimum {minimum_dpi}"
        )
    final_pixel_width = math.ceil(
        float(info["width_mm"]) / 25.4 * target_dpi
    )
    outputs: list[str] = []
    postprocess: dict[str, object] = {}

    if args.mode in {"preview", "all"}:
        preview = out_dir / f"{name}.png"
        command = [
            drawio,
            "-x",
            "-f",
            "png",
            "-s",
            str(args.scale),
            "-b",
            str(args.border),
            "-o",
            str(preview),
            str(figure),
        ]
        run(command, args.timeout)
        outputs.append(str(preview))

    if args.mode in {"final", "all"}:
        formats = [
            value.strip().lower()
            for value in args.formats.split(",")
            if value.strip()
        ]
        if not formats:
            raise SystemExit("--formats must name at least one final format")
        unsupported = set(formats) - {"svg", "pdf", "png", "jpg"}
        if unsupported:
            raise SystemExit(
                "unsupported final format(s): " + ", ".join(sorted(unsupported))
            )
        if not {"svg", "pdf"}.intersection(formats):
            raise SystemExit(
                "final academic exports require at least one vector master "
                "(svg or pdf)"
            )
        for export_format in formats:
            suffix = (
                f"{name}.drawio.png"
                if export_format == "png"
                else f"{name}.{export_format}"
            )
            output = out_dir / suffix
            command = [
                drawio,
                "-x",
                "-f",
                export_format,
                "-e",
                "-b",
                str(args.border),
            ]
            if export_format == "pdf":
                command.append("--crop")
            if export_format in {"png", "jpg"}:
                command.extend(["--width", str(final_pixel_width)])
            command.extend(["-o", str(output), str(figure)])
            run(command, args.timeout)
            if export_format == "png":
                postprocess["png_iend"] = repair_png(output)
                postprocess["png_dpi"] = round(
                    validate_png_dpi(
                        output,
                        float(info["width_mm"]),
                        minimum_dpi,
                    ),
                    1,
                )
            if export_format == "pdf":
                postprocess["pdf_size"] = normalize_pdf_size(
                    output,
                    info,
                    args.timeout,
                )
            if export_format == "svg":
                polish_svg(output, info)
                postprocess["svg_physical_width_mm"] = float(
                    info["width_mm"]
                )
            outputs.append(str(output))

    print(
        json.dumps(
            {
                "drawio_bin": drawio,
                "mode": args.mode,
                "outputs": outputs,
                "postprocess": postprocess,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
