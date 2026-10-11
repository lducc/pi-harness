#!/usr/bin/env python3
"""Regression tests for Draw.io academic-style hardening.

These tests use a temporary paper-icons catalog and never invoke Draw.io.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.parse import quote, unquote
from xml.etree import ElementTree as ET

SKILL_ROOT = Path(__file__).resolve().parent.parent
BUILDER = SKILL_ROOT / "scripts/build_drawio_figure.py"
PAPER_VALIDATOR = SKILL_ROOT / "scripts/validate_paper_palette.py"


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(
        name,
        SKILL_ROOT / "scripts" / filename,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_script("scientific_figure_validator", "validate_drawio_figure.py")
EXPORTER = load_script("scientific_figure_exporter", "export_drawio_figure.py")


class DrawioHardeningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        self.paper_icons = self.workspace / "paper-icons"
        icon_dir = self.paper_icons / "library/icons/lucide"
        icon_dir.mkdir(parents=True)
        (self.paper_icons / "SKILL.md").write_text(
            "# Test paper-icons\n",
            encoding="utf-8",
        )
        icon_markup = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
            'fill="none" stroke="currentColor" stroke-width="2">'
            '<path d="M4 12h16"/><path d="m14 6 6 6-6 6"/></svg>'
        )
        (icon_dir / "arrow.svg").write_text(icon_markup, encoding="utf-8")
        catalog = {
            "icons": [
                {
                    "id": "lucide-arrow-right",
                    "name": "Arrow right",
                    "category": "lucide",
                    "source": "Lucide",
                    "svg": "library/icons/lucide/arrow.svg",
                    "recolorable": True,
                }
            ]
        }
        (self.paper_icons / "library/catalog.json").write_text(
            json.dumps(catalog),
            encoding="utf-8",
        )
        self.spec = self.workspace / "figure.json"
        self.figure = self.workspace / "figure.drawio"
        self.manifest = self.workspace / "figure.icons.json"
        self.spec.write_text(
            json.dumps(
                {
                    "metadata": {
                        "title": "Hardening baseline",
                        "description": "Two-stage academic pipeline.",
                        "claim": "The validated path preserves provenance.",
                    },
                    "figure": {
                        "column": "double",
                        "layout": "pipeline",
                        "direction": "horizontal",
                    },
                    "nodes": [
                        {
                            "id": "input",
                            "label": "Task specification",
                            "subtitle": "Operator + constraints",
                            "icon": "lucide-arrow-right",
                            "tone": "accent",
                        },
                        {
                            "id": "result",
                            "label": "Result",
                            "tone": "success",
                        },
                    ],
                    "edges": [
                        {
                            "from": "input",
                            "to": "result",
                            "relation": "produces",
                            "label": "validated",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(BUILDER),
                str(self.spec),
                "--out",
                str(self.figure),
                "--paper-icons-skill",
                str(self.paper_icons),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def validate(self) -> tuple[list[str], list[str], dict]:
        return VALIDATOR.validate(self.figure, self.manifest)

    def write_palette(
        self,
        *,
        status: str = "frozen",
        paper_id: str = "hardening-paper",
    ) -> Path:
        palette = self.workspace / "paper-palette.yaml"
        palette.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "palette_id": "hardening-paper-v1",
                    "paper_id": paper_id,
                    "status": status,
                    "description": "Test paper palette.",
                    "semantic": {
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
                    },
                    "chart_roles": {
                        "ours": "#2563EB",
                        "baseline": "#64748B",
                    },
                    "rules": {
                        "same_entity_same_color_across_figures": True,
                        "maximum_semantic_hues": 5,
                    },
                }
            ),
            encoding="utf-8",
        )
        return palette

    def build_with_palette(
        self,
        output: Path,
        palette: Path,
        spec: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(BUILDER),
                str(spec or self.spec),
                "--out",
                str(output),
                "--paper-icons-skill",
                str(self.paper_icons),
                "--paper-palette",
                str(palette),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def mutate_cell(self, cell_id: str, mutate) -> None:
        tree = ET.parse(self.figure)
        cell = tree.getroot().find(
            f"./diagram/mxGraphModel/root/mxCell[@id='{cell_id}']"
        )
        self.assertIsNotNone(cell)
        mutate(cell)
        tree.write(self.figure, encoding="utf-8", xml_declaration=True)

    def test_baseline_is_strict_clean_and_manifest_binds_payload(self) -> None:
        errors, warnings, _ = self.validate()
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        payload = json.loads(self.manifest.read_text(encoding="utf-8"))
        digest = payload["icons"][0]["payload_sha256"]
        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        self.assertNotIn(str(self.workspace), self.manifest.read_text())
        self.assertTrue(
            payload["icons"][0]["source_svg"].startswith("paper-icons://")
        )

    def test_pipeline_reserves_space_for_wrapped_academic_labels(self) -> None:
        tree = ET.parse(self.figure)
        root = tree.getroot()
        node_geometry = root.find(
            "./diagram/mxGraphModel/root/"
            "mxCell[@id='node-input']/mxGeometry"
        )
        label_geometry = root.find(
            "./diagram/mxGraphModel/root/"
            "mxCell[@id='label-input']/mxGeometry"
        )
        self.assertIsNotNone(node_geometry)
        self.assertIsNotNone(label_geometry)
        node_height = float(node_geometry.get("height", "0"))
        label_y = float(label_geometry.get("y", "0"))
        label_height = float(label_geometry.get("height", "0"))
        self.assertGreaterEqual(node_height, 170.0)
        self.assertGreaterEqual(label_height, 95.0)
        self.assertLessEqual(label_y + label_height, node_height - 9.0)

    def test_edge_requires_present_nonempty_relation(self) -> None:
        self.mutate_cell(
            "edge-1",
            lambda cell: cell.attrib.pop("data-relation"),
        )
        errors, _, _ = self.validate()
        self.assertTrue(any("data-relation" in error for error in errors))
        self.mutate_cell(
            "edge-1",
            lambda cell: cell.set("data-relation", "   "),
        )
        errors, _, _ = self.validate()
        self.assertTrue(any("data-relation" in error for error in errors))

    def test_inline_css_color_is_contrast_checked_and_hidden_text_rejected(
        self,
    ) -> None:
        self.mutate_cell(
            "label-input",
            lambda cell: cell.set(
                "value",
                '<span style="color:#FFFFFF; display:none">Input</span>',
            ),
        )
        errors, warnings, _ = self.validate()
        self.assertTrue(any("display:none" in error for error in errors))
        self.assertTrue(
            any("text contrast" in warning for warning in warnings)
        )

    def test_drawio_and_inline_opacity_must_be_fully_visible(self) -> None:
        self.mutate_cell(
            "node-input",
            lambda cell: cell.set(
                "style",
                cell.get("style", "") + "opacity=opaque;",
            ),
        )

        def add_text_opacity(cell: ET.Element) -> None:
            cell.set(
                "style",
                cell.get("style", "") + "textOpacity=99;",
            )
            cell.set(
                "value",
                '<span style="opacity:0.5">Input</span>',
            )

        self.mutate_cell("label-input", add_text_opacity)
        errors, _, _ = self.validate()
        self.assertTrue(any("textOpacity=99" in error for error in errors))
        self.assertTrue(any("invalid opacity='opaque'" in error for error in errors))
        self.assertTrue(any("inline CSS opacity=0.5" in error for error in errors))

    def test_embedded_svg_payload_replacement_breaks_manifest_binding(
        self,
    ) -> None:
        def replace_payload(cell: ET.Element) -> None:
            parts = VALIDATOR.parse_style(cell.get("style", ""))
            encoded = parts["image"].split(",", 1)[1]
            payload = unquote(encoded).replace(
                '<path d="M4 12h16"/>',
                '<circle cx="12" cy="12" r="8"/>',
            )
            parts["image"] = "data:image/svg+xml," + quote(payload, safe="")
            cell.set(
                "style",
                ";".join(f"{key}={value}" for key, value in parts.items()) + ";",
            )

        self.mutate_cell("icon-input", replace_payload)
        errors, _, _ = self.validate()
        self.assertTrue(
            any("payload SHA-256" in error for error in errors)
        )

    def test_paper_palette_id_and_digest_bind_to_figure(self) -> None:
        palette = self.write_palette()
        figure = self.workspace / "bound.drawio"
        result = self.build_with_palette(figure, palette)
        self.assertEqual(result.returncode, 0, result.stderr)
        errors, warnings, summary = VALIDATOR.validate(
            figure,
            paper_palette_path=palette,
        )
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertTrue(summary["paper_palette_verified"])
        self.assertEqual(
            summary["paper_palette_id"],
            "hardening-paper-v1",
        )
        self.assertRegex(
            summary["paper_palette_sha256"],
            r"^[0-9a-f]{64}$",
        )
        _, unverified_warnings, unverified_summary = VALIDATOR.validate(figure)
        self.assertTrue(
            any("was not verified" in warning for warning in unverified_warnings)
        )
        self.assertFalse(unverified_summary["paper_palette_verified"])

    def test_bound_paper_palette_rejects_per_figure_color_drift(self) -> None:
        palette = self.write_palette()
        drift_spec = self.workspace / "drift.json"
        payload = json.loads(self.spec.read_text(encoding="utf-8"))
        payload["figure"]["palette"] = {"accent": "#FF00AA"}
        drift_spec.write_text(json.dumps(payload), encoding="utf-8")
        result = self.build_with_palette(
            self.workspace / "drift.drawio",
            palette,
            drift_spec,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot drift", result.stderr + result.stdout)

    def test_cross_figure_palette_audit_requires_one_frozen_contract(
        self,
    ) -> None:
        palette = self.write_palette()
        first = self.workspace / "figure-one.drawio"
        second = self.workspace / "figure-two.drawio"
        self.assertEqual(
            self.build_with_palette(first, palette).returncode,
            0,
        )
        self.assertEqual(
            self.build_with_palette(second, palette).returncode,
            0,
        )
        result = subprocess.run(
            [
                sys.executable,
                str(PAPER_VALIDATOR),
                "--palette",
                str(palette),
                str(first),
                str(second),
                "--strict",
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["figure_count"], 2)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["warnings"], [])

    def test_final_pdf_normalization_fails_without_ghostscript(self) -> None:
        info = {
            "width_mm": "178",
            "page_width": "1080",
            "page_height": "480",
        }
        with mock.patch.object(EXPORTER.shutil, "which", return_value=None):
            with self.assertRaisesRegex(SystemExit, "requires Ghostscript"):
                EXPORTER.normalize_pdf_size(
                    self.workspace / "figure.pdf",
                    info,
                    10,
                )


if __name__ == "__main__":
    unittest.main()
