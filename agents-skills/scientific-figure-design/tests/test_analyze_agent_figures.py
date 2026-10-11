#!/usr/bin/env python3
"""Tests for the caption-derived AI-agent figure audit."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent


def load_script():
    path = SKILL_ROOT / "scripts/analyze_agent_figures.py"
    spec = importlib.util.spec_from_file_location("agent_figure_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import analyze_agent_figures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = load_script()


class AgentFigureAuditTests(unittest.TestCase):
    def test_caption_tags_detect_nested_evolution_evidence(self) -> None:
        caption = (
            "System overview with a fast task-skill loop, a slower meta-skill "
            "update, verifier feedback, persistent memory, and held-out results."
        )
        tags = set(AUDIT.caption_tags(caption, "system-overview"))
        self.assertIn("system-and-loop", tags)
        self.assertIn("timescale-or-stage", tags)
        self.assertIn("critic-or-gate", tags)
        self.assertIn("persistence", tags)
        self.assertIn("transfer-and-generalization", tags)
        self.assertIn("result-comparison", tags)

    def test_analysis_combines_main_and_ar5iv_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fallback = root / "fallback/ar5iv"
            fallback.mkdir(parents=True)
            main_figure = {
                "arxiv_id": "2501.00001",
                "paper_title": "Evolving Agent",
                "figure_index": 1,
                "figure_type": "system-overview",
                "caption": (
                    "Overview of an iterative policy and data evolution loop "
                    "with verifier feedback."
                ),
                "images": [{"local_path": "papers/a/figure-1.png"}],
            }
            fallback_figure = {
                "arxiv_id": "2501.00002",
                "paper_title": "Transfer Agent",
                "figure_index": 2,
                "figure_type": "quantitative-comparison",
                "caption": (
                    "Cross-task transfer results on held-out environments."
                ),
                "images": [{"local_path": "papers/b/figure-2.svg"}],
            }
            (root / "figures.jsonl").write_text(
                json.dumps(main_figure) + "\n",
                encoding="utf-8",
            )
            (fallback / "figures.jsonl").write_text(
                json.dumps(fallback_figure) + "\n",
                encoding="utf-8",
            )

            result = AUDIT.analyze(root)

            self.assertEqual(result["paper_count"], 2)
            self.assertEqual(result["figure_count"], 2)
            first = result["papers"][0]
            self.assertIn("mechanism", first["present_review_roles"])
            self.assertIn(
                "selection_or_feedback",
                first["present_review_roles"],
            )
            second = result["papers"][1]
            self.assertIn("outcome_evidence", second["present_review_roles"])
            self.assertIn(
                "robustness_evidence",
                second["present_review_roles"],
            )


if __name__ == "__main__":
    unittest.main()
