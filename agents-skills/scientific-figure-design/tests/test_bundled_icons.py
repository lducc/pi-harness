#!/usr/bin/env python3
"""Integrity and licensing checks for the bundled paper icon catalog."""

from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICON_ROOT = ROOT / "assets/paper-icons"
LIBRARY = ICON_ROOT / "library"


class BundledIconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads(
            (LIBRARY / "catalog.json").read_text(encoding="utf-8")
        )
        cls.license_manifest = json.loads(
            (LIBRARY / "license-manifest.json").read_text(encoding="utf-8")
        )
        cls.icons = cls.catalog["icons"]

    def test_catalog_has_581_unique_resolvable_svg_icons(self) -> None:
        self.assertEqual(len(self.icons), 581)
        ids = [icon["id"] for icon in self.icons]
        self.assertEqual(len(ids), len(set(ids)))
        missing = [
            icon["svg"]
            for icon in self.icons
            if not (ICON_ROOT / icon["svg"]).is_file()
        ]
        self.assertEqual(missing, [])

    def test_catalog_sources_match_audited_inventory(self) -> None:
        sources = Counter(icon["source"] for icon in self.icons)
        self.assertEqual(
            sources,
            {
                "original": 37,
                "ml-paper-icons (MIT)": 512,
                "Lucide (ISC), fetched on demand": 32,
            },
        )

    def test_license_groups_match_filesystem_inventory(self) -> None:
        self.assertEqual(
            self.license_manifest["total_catalog_icons"],
            len(self.icons),
        )
        group_total = 0
        for group in self.license_manifest["groups"]:
            files = {
                path
                for pattern in group["paths"]
                for path in LIBRARY.glob(pattern)
                if path.is_file()
            }
            self.assertEqual(
                len(files),
                group["count"],
                f"license inventory drift for {group['paths']}",
            )
            group_total += group["count"]
        self.assertEqual(group_total, len(self.icons))

    def test_color_brand_marks_are_not_recolorable(self) -> None:
        protected = [
            icon
            for icon in self.icons
            if icon["category"] == "brand"
            and icon["color_type"] == "color"
        ]
        self.assertEqual(len(protected), 32)
        self.assertTrue(all(icon["recolorable"] is False for icon in protected))

    def test_svg_sources_do_not_embed_raster_or_html(self) -> None:
        unsafe = []
        for icon in self.icons:
            markup = (ICON_ROOT / icon["svg"]).read_text(
                encoding="utf-8",
                errors="replace",
            )
            lowered = markup.lower()
            if "<foreignobject" in lowered or "<image " in lowered:
                unsafe.append(icon["id"])
        self.assertEqual(unsafe, [])


if __name__ == "__main__":
    unittest.main()
