#!/usr/bin/env python3
"""Audit figure roles in AI-agent and self-evolution paper corpora.

The audit is intentionally caption-derived. It helps reviewers find candidate
figures and missing evidence roles, but it does not replace visual inspection.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

TAG_PATTERNS = {
    "system-and-loop": (
        r"\bframework\b",
        r"\boverview\b",
        r"\bpipeline\b",
        r"\bclosed[- ]loop\b",
        r"\bself[- ]evol",
        r"\bco[- ]evol",
        r"\biterative\b",
        r"\bcycle\b",
    ),
    "mutable-state": (
        r"\bpolicy\b",
        r"\bmodel\b",
        r"\bdata(?:set)?\b",
        r"\btask\b",
        r"\bprompt\b",
        r"\bmemory\b",
        r"\bskill\b",
        r"\btool\b",
        r"\basset\b",
        r"\btopolog",
        r"\barchitecture\b",
        r"\bexperience\b",
        r"\bcritic\b",
    ),
    "timescale-or-stage": (
        r"\bphase\b",
        r"\biteration\b",
        r"\bround\b",
        r"\bstage\b",
        r"\bfast loop\b",
        r"\bslow(?:er)?\b",
        r"\binner loop\b",
        r"\bouter loop\b",
        r"\bintra[- ]test\b",
        r"\binter[- ]test\b",
        r"\bupdate\b",
    ),
    "search-or-topology": (
        r"\bsearch\b",
        r"\btree\b",
        r"\bgraph\b",
        r"\btopolog",
        r"\bfrontier\b",
        r"\bmcts\b",
        r"\boperator\b",
        r"\bcandidate\b",
        r"\bbranch\b",
    ),
    "critic-or-gate": (
        r"\bverif",
        r"\bcritic\b",
        r"\breward\b",
        r"\bfeedback\b",
        r"\bfilter",
        r"\bvalid",
        r"\bselect",
        r"\baccept",
        r"\breject",
        r"\bsuccess",
        r"\bfailure",
    ),
    "persistence": (
        r"\bmemory\b",
        r"\bskill(?:bank| library)?\b",
        r"\blibrary\b",
        r"\bbuffer\b",
        r"\bdatabase\b",
        r"\bstore\b",
        r"\bretriev",
        r"\bdistill",
        r"\basset\b",
    ),
    "evolution-dynamics": (
        r"\bevolution of\b",
        r"\bduring (?:rl )?training\b",
        r"\btraining progresses\b",
        r"\bover (?:training )?iterations\b",
        r"\bnumber of phases\b",
        r"\blearning curve\b",
        r"\bcumulative\b",
        r"\bprogressive evolution\b",
        r"\bdynamics\b",
    ),
    "result-comparison": (
        r"\bperformance\b",
        r"\baccuracy\b",
        r"\bsuccess rate\b",
        r"\bcomparison\b",
        r"\boutperform",
        r"\bresults?\b",
        r"\bablation\b",
        r"\bevaluation\b",
    ),
    "transfer-and-generalization": (
        r"\bcross[- ]task\b",
        r"\bcross[- ]framework\b",
        r"\bcross[- ]model\b",
        r"\btransfer",
        r"\bgenerali[sz]",
        r"\bunseen\b",
        r"\bout[- ]of[- ]distribution\b",
        r"\bheld[- ]out\b",
    ),
    "failure-and-stability": (
        r"\bfailure\b",
        r"\berror\b",
        r"\bforget",
        r"\bcollapse\b",
        r"\bstabil",
        r"\brobust",
        r"\bdistribution shift\b",
        r"\binvalid\b",
        r"\bregression\b",
    ),
    "worked-trace": (
        r"\bexample\b",
        r"\bcase stud",
        r"\btrajectory\b",
        r"\bprompt\b",
        r"\bdemonstration\b",
        r"\billustration of how\b",
    ),
    "taxonomy-or-landscape": (
        r"\btaxonomy\b",
        r"\blandscape\b",
        r"\bcategori[sz]ation\b",
        r"\bsurvey\b",
        r"\brepresentative methods\b",
    ),
}

FIGURE_TYPE_TAGS = {
    "system-overview": {"system-and-loop"},
    "training-process": {"timescale-or-stage", "evolution-dynamics"},
    "quantitative-comparison": {"result-comparison"},
    "ablation": {"result-comparison"},
    "scaling": {"result-comparison"},
    "worked-example": {"worked-trace"},
    "dataset-or-taxonomy": {"taxonomy-or-landscape"},
}

REVIEW_ROLES = {
    "mechanism": {"system-and-loop"},
    "mutable_object": {"mutable-state"},
    "temporal_change": {"timescale-or-stage", "evolution-dynamics"},
    "selection_or_feedback": {"critic-or-gate"},
    "persistent_state": {"persistence"},
    "outcome_evidence": {"result-comparison"},
    "robustness_evidence": {
        "transfer-and-generalization",
        "failure-and-stability",
    },
    "concrete_trace": {"worked-trace"},
}


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def discover_figures(root: Path) -> list[dict]:
    sources = [
        (root, root / "figures.jsonl"),
        (
            root / "fallback" / "ar5iv",
            root / "fallback" / "ar5iv" / "figures.jsonl",
        ),
    ]
    figures = []
    for collection_root, source in sources:
        for figure in load_jsonl(source):
            figure = dict(figure)
            figure["_collection_root"] = str(collection_root)
            figures.append(figure)
    return figures


def caption_tags(caption: str, figure_type: str = "") -> list[str]:
    text = " ".join(caption.lower().split())
    tags = {
        tag
        for tag, patterns in TAG_PATTERNS.items()
        if any(re.search(pattern, text) for pattern in patterns)
    }
    tags.update(FIGURE_TYPE_TAGS.get(figure_type, set()))
    return sorted(tags)


def representative_score(figure: dict, tags: set[str]) -> tuple[int, int]:
    score = 0
    if "system-and-loop" in tags:
        score += 6
    if "mutable-state" in tags:
        score += 3
    if "timescale-or-stage" in tags:
        score += 2
    if "critic-or-gate" in tags:
        score += 2
    if "result-comparison" in tags:
        score += 1
    figure_index = int(figure.get("figure_index", 999))
    return score, -figure_index


def analyze(root: Path) -> dict:
    figures = discover_figures(root)
    grouped: dict[str, list[dict]] = defaultdict(list)
    global_tags: Counter[str] = Counter()

    for figure in figures:
        tags = caption_tags(
            str(figure.get("caption", "")),
            str(figure.get("figure_type", "")),
        )
        enriched = dict(figure)
        enriched["agent_tags"] = tags
        grouped[str(figure["arxiv_id"])].append(enriched)
        global_tags.update(tags)

    papers = []
    for arxiv_id, paper_figures in sorted(grouped.items()):
        paper_figures.sort(key=lambda item: int(item.get("figure_index", 999)))
        paper_tags = Counter(
            tag for figure in paper_figures for tag in figure["agent_tags"]
        )
        present_roles = []
        review_gaps = []
        for role, accepted_tags in REVIEW_ROLES.items():
            if accepted_tags.intersection(paper_tags):
                present_roles.append(role)
            else:
                review_gaps.append(role)

        representative = max(
            paper_figures,
            key=lambda item: representative_score(
                item,
                set(item["agent_tags"]),
            ),
        )
        papers.append(
            {
                "arxiv_id": arxiv_id,
                "title": paper_figures[0].get("paper_title", ""),
                "figure_count": len(paper_figures),
                "tag_counts": dict(sorted(paper_tags.items())),
                "present_review_roles": present_roles,
                "caption_derived_review_gaps": review_gaps,
                "representative_figure": {
                    "figure_index": representative.get("figure_index"),
                    "figure_type": representative.get("figure_type"),
                    "caption": representative.get("caption", ""),
                    "images": [
                        image.get("local_path")
                        for image in representative.get("images", [])
                        if image.get("local_path")
                    ],
                },
            }
        )

    return {
        "method": (
            "Caption-derived review aid. Tags and gaps require visual and "
            "paper-context confirmation."
        ),
        "paper_count": len(papers),
        "figure_count": len(figures),
        "tag_counts": dict(sorted(global_tags.items())),
        "papers": papers,
    }


def markdown_report(result: dict) -> str:
    lines = [
        "# AI-agent figure-role audit",
        "",
        f"> {result['method']}",
        "",
        "## Corpus",
        "",
        f"- Papers with structured figures: {result['paper_count']}",
        f"- Figure groups: {result['figure_count']}",
        "",
        "## Caption tags",
        "",
        "| Tag | Figure groups |",
        "| --- | ---: |",
    ]
    for tag, count in result["tag_counts"].items():
        lines.append(f"| {tag} | {count} |")

    lines.extend(
        [
            "",
            "## Per-paper review",
            "",
            "| arXiv | Figures | Present roles | Caption-derived review gaps | "
            "Representative |",
            "| --- | ---: | --- | --- | --- |",
        ]
    )
    for paper in result["papers"]:
        representative = paper["representative_figure"]
        present = ", ".join(paper["present_review_roles"]) or "none detected"
        gaps = (
            ", ".join(paper["caption_derived_review_gaps"])
            or "none detected"
        )
        figure_label = (
            f"Fig. {representative['figure_index']} "
            f"({representative['figure_type']})"
        )
        lines.append(
            f"| {paper['arxiv_id']} | {paper['figure_count']} | {present} | "
            f"{gaps} | {figure_label} |"
        )

    lines.extend(
        [
            "",
            "Use the gaps as questions for manual review, not as automatic "
            "failures. Captions can omit semantics that are visible in the "
            "figure or explained in nearby prose.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    result = analyze(root)
    (output_dir / "agent-figure-audit.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "agent-figure-audit.md").write_text(
        markdown_report(result),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "paper_count": result["paper_count"],
                "figure_count": result["figure_count"],
                "output_dir": str(output_dir),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
