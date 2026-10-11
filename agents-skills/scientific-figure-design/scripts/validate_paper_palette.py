#!/usr/bin/env python3
"""Audit Draw.io figures against one frozen paper-level color contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_drawio_figure import read_academic_style, read_paper_palette, validate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "figures",
        nargs="+",
        type=Path,
        help="Draw.io sources belonging to the same paper.",
    )
    parser.add_argument(
        "--palette",
        required=True,
        type=Path,
        help="Shared paper-palette.yaml contract.",
    )
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    palette_path = args.palette.resolve()
    try:
        academic_style = read_academic_style()
        palette, digest = read_paper_palette(
            palette_path,
            academic_style,
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SystemExit(
            f"cannot read paper palette {palette_path}: {exc}"
        ) from exc

    errors: list[str] = []
    warnings: list[str] = []
    figure_results: list[dict] = []
    all_semantic_colors: set[str] = set()
    resolved_figures: list[Path] = []
    for raw_figure in args.figures:
        figure = raw_figure.resolve()
        if figure in resolved_figures:
            continue
        resolved_figures.append(figure)
        figure_errors, figure_warnings, summary = validate(
            figure,
            paper_palette_path=palette_path,
        )
        errors.extend(
            f"{figure}: {message}"
            for message in figure_errors
        )
        warnings.extend(
            f"{figure}: {message}"
            for message in figure_warnings
        )
        all_semantic_colors.update(summary.get("semantic_colors", []))
        figure_results.append(
            {
                "figure": str(figure),
                "errors": figure_errors,
                "warnings": figure_warnings,
                "semantic_colors": summary.get("semantic_colors", []),
                "palette_verified": summary.get(
                    "paper_palette_verified",
                    False,
                ),
            }
        )

    if len(resolved_figures) > 1 and palette["status"] != "frozen":
        warnings.append(
            "multi-figure audit requires paper palette status=frozen"
        )
    if len(resolved_figures) > 1 and not palette.get("paper_id"):
        warnings.append(
            "multi-figure audit requires a non-empty paper_id"
        )

    result = {
        "palette": str(palette_path),
        "palette_id": palette["palette_id"],
        "paper_id": palette.get("paper_id", ""),
        "status": palette["status"],
        "sha256": digest,
        "figure_count": len(resolved_figures),
        "semantic_colors_used": sorted(all_semantic_colors),
        "errors": errors,
        "warnings": warnings,
        "figures": figure_results,
    }
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for error in errors:
            print(f"ERROR: {error}")
        for warning in warnings:
            print(f"WARNING: {warning}")
        print(
            f"{len(resolved_figures)} figure(s), "
            f"{len(errors)} error(s), {len(warnings)} warning(s), "
            f"palette={palette['palette_id']} sha256={digest}"
        )
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
