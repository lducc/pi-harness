#!/usr/bin/env python3
"""Compute visual statistics and create sampled contact sheets."""

from __future__ import annotations

import argparse
import io
import json
import math
import statistics
import textwrap
from collections import Counter, defaultdict
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFile, ImageFont, ImageOps

ImageFile.LOAD_TRUNCATED_IMAGES = True


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def detect_tool(path: Path, image_info: dict | None = None) -> str:
    if image_info:
        software = str(image_info.get("Software", ""))
        if "matplotlib" in software.lower():
            return "Matplotlib"
        if software:
            return f"Metadata:{software[:80]}"
    if path.suffix.lower() == ".svg":
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if "matplotlib" in text:
            return "Matplotlib"
        if "graphviz" in text:
            return "Graphviz"
        if "inkscape" in text:
            return "Inkscape"
        if "adobe illustrator" in text:
            return "Adobe Illustrator"
        if "ltx_picture" in text or "ltx_" in text:
            return "LaTeXML/TikZ"
    return "Unknown"


def open_visual(path: Path, width: int = 700) -> tuple[Image.Image, dict]:
    if path.suffix.lower() == ".svg":
        png = cairosvg.svg2png(url=str(path), output_width=width)
        image = Image.open(io.BytesIO(png))
        info = {}
    else:
        image = Image.open(path)
        info = dict(image.info)
    if image.mode == "RGBA":
        canvas = Image.new("RGBA", image.size, "white")
        canvas.alpha_composite(image)
        image = canvas.convert("RGB")
    else:
        image = image.convert("RGB")
    return image, info


def image_metrics(path: Path) -> dict:
    image, info = open_visual(path, width=512)
    width, height = image.size
    sample = image.copy()
    sample.thumbnail((256, 256), Image.Resampling.LANCZOS)
    pixels = list(sample.getdata())
    count = max(1, len(pixels))
    white = sum(min(pixel) >= 245 for pixel in pixels) / count
    grayscale = sum(max(pixel) - min(pixel) <= 8 for pixel in pixels) / count
    dark = sum(max(pixel) <= 48 for pixel in pixels) / count
    hsv = sample.convert("HSV")
    saturation = sum(pixel[1] >= 64 for pixel in hsv.getdata()) / count
    return {
        "width": width,
        "height": height,
        "aspect_ratio": width / max(1, height),
        "white_fraction": white,
        "grayscale_fraction": grayscale,
        "dark_fraction": dark,
        "saturated_fraction": saturation,
        "tool_evidence": detect_tool(path, info),
        "metadata_keys": sorted(
            key for key in info if key not in {"icc_profile", "exif"}
        ),
    }


def html_assets(
    collection_root: Path,
    papers_path: Path,
) -> tuple[list[dict], list[dict]]:
    assets = []
    figures = []
    for paper in load_json(papers_path):
        if paper["status"] != "ok":
            continue
        for figure in paper.get("figures", []):
            successful = [
                asset
                for asset in figure.get("images", [])
                if asset["status"] in {"downloaded", "extracted"}
            ]
            figures.append(
                {
                    "arxiv_id": paper["arxiv_id"],
                    "figure_type": figure["figure_type"],
                    "asset_count": len(successful),
                    "caption": figure["caption"],
                }
            )
            for asset in successful:
                assets.append(
                    {
                        "arxiv_id": paper["arxiv_id"],
                        "paper_title": paper["title"],
                        "figure_index": figure["figure_index"],
                        "figure_label": figure["label"],
                        "figure_type": figure["figure_type"],
                        "caption": figure["caption"],
                        "subfigure_label": asset.get("subfigure_label"),
                        "subfigure_caption": asset.get("subfigure_caption"),
                        "path": collection_root / asset["local_path"],
                    }
                )
    return assets, figures


def evenly_sample(items: list[dict], limit: int) -> list[dict]:
    if len(items) <= limit:
        return items
    if limit == 1:
        return [items[0]]
    indices = {
        round(index * (len(items) - 1) / (limit - 1))
        for index in range(limit)
    }
    return [items[index] for index in sorted(indices)]


def load_font(size: int):
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/Helvetica.ttc"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def create_contact_sheets(
    groups: dict[str, list[dict]],
    output_dir: Path,
    per_group: int,
) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    tile_width, tile_height = 560, 420
    cols, rows = 4, 4
    title_height = 54
    font = load_font(18)
    small_font = load_font(15)
    index_records = []
    for group, all_items in sorted(groups.items()):
        items = evenly_sample(
            sorted(
                all_items,
                key=lambda item: (
                    item.get("arxiv_id", ""),
                    item.get("figure_index", 0),
                    str(item["path"]),
                ),
            ),
            per_group,
        )
        for page_index in range(math.ceil(len(items) / (cols * rows))):
            page_items = items[
                page_index * cols * rows : (page_index + 1) * cols * rows
            ]
            sheet = Image.new(
                "RGB",
                (cols * tile_width, title_height + rows * tile_height),
                "#F4F2ED",
            )
            draw = ImageDraw.Draw(sheet)
            draw.text(
                (22, 16),
                f"{group} - sampled {len(items)} / {len(all_items)} assets",
                fill="#171717",
                font=font,
            )
            for slot, item in enumerate(page_items):
                row, col = divmod(slot, cols)
                x = col * tile_width
                y = title_height + row * tile_height
                draw.rounded_rectangle(
                    (x + 8, y + 8, x + tile_width - 8, y + tile_height - 8),
                    radius=12,
                    fill="white",
                    outline="#D0CDC6",
                    width=2,
                )
                try:
                    image, _ = open_visual(item["path"], width=500)
                    fitted = ImageOps.contain(
                        image,
                        (tile_width - 36, 280),
                        Image.Resampling.LANCZOS,
                    )
                    image_x = x + (tile_width - fitted.width) // 2
                    sheet.paste(fitted, (image_x, y + 22))
                except Exception as exc:
                    draw.text(
                        (x + 22, y + 32),
                        f"Render error: {exc}",
                        fill="#A02020",
                        font=small_font,
                    )
                label = (
                    f"{item.get('arxiv_id', '')}  "
                    f"Fig.{item.get('figure_index', '-')}"
                    f"{item.get('subfigure_label') or ''}"
                )
                draw.text(
                    (x + 20, y + 314),
                    label,
                    fill="#111111",
                    font=font,
                )
                caption = (
                    item.get("subfigure_caption")
                    or item.get("caption")
                    or item["path"].name
                )
                wrapped = "\n".join(
                    textwrap.wrap(caption, width=62)[:3]
                )
                draw.multiline_text(
                    (x + 20, y + 342),
                    wrapped,
                    fill="#4A4A4A",
                    font=small_font,
                    spacing=3,
                )
                index_records.append(
                    {
                        "group": group,
                        "sheet": f"{group}-{page_index + 1:02d}.jpg",
                        "slot": slot + 1,
                        "arxiv_id": item.get("arxiv_id"),
                        "figure_index": item.get("figure_index"),
                        "path": str(item["path"]),
                        "caption": caption,
                    }
                )
            sheet.save(
                output_dir / f"{group}-{page_index + 1:02d}.jpg",
                quality=90,
                optimize=True,
            )
    return index_records


def aggregate_metrics(records: list[dict]) -> dict:
    by_type: dict[str, list[dict]] = defaultdict(list)
    tool_counts = Counter()
    format_counts = Counter()
    for record in records:
        by_type[record["figure_type"]].append(record["metrics"])
        tool_counts[record["metrics"]["tool_evidence"]] += 1
        format_counts[record["path"].suffix.lower()] += 1

    def summarise(metrics: list[dict]) -> dict:
        return {
            "asset_count": len(metrics),
            "median_aspect_ratio": round(
                statistics.median(item["aspect_ratio"] for item in metrics), 3
            ),
            "mean_white_fraction": round(
                statistics.fmean(item["white_fraction"] for item in metrics), 3
            ),
            "mean_grayscale_fraction": round(
                statistics.fmean(item["grayscale_fraction"] for item in metrics),
                3,
            ),
            "mean_saturated_fraction": round(
                statistics.fmean(item["saturated_fraction"] for item in metrics),
                3,
            ),
        }

    return {
        "asset_count": len(records),
        "format_counts": dict(sorted(format_counts.items())),
        "tool_evidence_counts": dict(tool_counts.most_common()),
        "by_figure_type": {
            figure_type: summarise(metrics)
            for figure_type, metrics in sorted(by_type.items())
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sample-per-type", type=int, default=32)
    args = parser.parse_args()
    root = args.root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    main_assets, main_figures = html_assets(root, root / "papers.json")
    ar5iv_root = root / "fallback" / "ar5iv"
    ar5iv_assets, ar5iv_figures = html_assets(
        ar5iv_root,
        ar5iv_root / "papers.json",
    )
    assets = main_assets + ar5iv_assets
    enriched = []
    for index, asset in enumerate(assets, start=1):
        try:
            metrics = image_metrics(asset["path"])
            enriched.append({**asset, "metrics": metrics})
        except Exception as exc:
            enriched.append(
                {
                    **asset,
                    "metrics": {
                        "width": 0,
                        "height": 0,
                        "aspect_ratio": 0,
                        "white_fraction": 0,
                        "grayscale_fraction": 0,
                        "dark_fraction": 0,
                        "saturated_fraction": 0,
                        "tool_evidence": f"Unreadable:{type(exc).__name__}",
                        "metadata_keys": [],
                    },
                }
            )
        if index % 100 == 0:
            print(f"metrics {index}/{len(assets)}", flush=True)

    figures = main_figures + ar5iv_figures
    panel_counts = Counter(figure["asset_count"] for figure in figures)
    statistics_result = {
        "paper_count": len({asset["arxiv_id"] for asset in enriched}),
        "figure_count": len(figures),
        "html_only_figure_count": sum(
            figure["asset_count"] == 0 for figure in figures
        ),
        "panel_asset_count_distribution": {
            str(key): value for key, value in sorted(panel_counts.items())
        },
        **aggregate_metrics(enriched),
    }
    (output_dir / "visual-stats.json").write_text(
        json.dumps(statistics_result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    groups: dict[str, list[dict]] = defaultdict(list)
    for asset in enriched:
        groups[asset["figure_type"]].append(asset)

    fallback_items = []
    for path in sorted(
        (root / "fallback" / "source").glob("*/assets/rendered/**/*.png")
    ):
        fallback_items.append(
            {
                "arxiv_id": path.relative_to(
                    root / "fallback" / "source"
                ).parts[0],
                "figure_index": 0,
                "figure_type": "pdf-source-fallback",
                "caption": path.stem,
                "path": path,
            }
        )
    for path in sorted(
        (root / "fallback" / "source").glob("*/assets/original/**/*")
    ):
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".svg"}:
            continue
        fallback_items.append(
            {
                "arxiv_id": path.relative_to(
                    root / "fallback" / "source"
                ).parts[0],
                "figure_index": 0,
                "figure_type": "pdf-source-fallback",
                "caption": path.stem,
                "path": path,
            }
        )
    groups["pdf-source-fallback"] = fallback_items
    index_records = create_contact_sheets(
        groups,
        output_dir / "contact-sheets",
        args.sample_per_type,
    )
    (output_dir / "contact-sheet-index.json").write_text(
        json.dumps(index_records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "asset_count": len(enriched),
                "contact_sheet_count": len(
                    {record["sheet"] for record in index_records}
                ),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
