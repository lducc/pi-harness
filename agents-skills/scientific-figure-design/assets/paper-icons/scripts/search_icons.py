#!/usr/bin/env python3
"""Rank paper-icons catalog entries by a semantic text query.

Examples:
  python3 search_icons.py "vector database retrieval" --limit 8
  python3 search_icons.py "模型训练" --family lucide --recolorable
  python3 search_icons.py "baseline model" --category brand --json
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOG = HERE.parent / "library" / "catalog.json"

# Compact bilingual expansion for common paper-figure concepts. Keep this focused:
# filenames and catalog metadata remain the source of truth.
ALIASES = {
    "数据": "data dataset database storage",
    "数据集": "dataset data database",
    "知识库": "knowledge base database retrieval",
    "向量库": "vector database storage retrieval",
    "模型": "model brain neural network",
    "训练": "training learning finetune model",
    "微调": "finetune training learning",
    "推理": "inference serving model",
    "评估": "evaluation benchmark target metric",
    "基准": "benchmark baseline evaluation",
    "检索": "retrieval search database",
    "搜索": "search retrieval",
    "智能体": "agent robot automation",
    "代理": "agent robot automation",
    "用户": "user human person",
    "反馈": "feedback loop refresh update",
    "优化": "optimization improve speed performance",
    "编译": "compiler build code",
    "执行": "execute runtime cpu play",
    "安全": "safety trusted shield lock",
    "成本": "cost budget wallet",
    "延迟": "latency time clock speed",
    "吞吐": "throughput speed performance",
    "成功": "success check pass",
    "失败": "failure cross error x",
    "论文": "paper article document",
    "图表": "chart graph visualization",
}


def tokenize(text: str) -> list[str]:
    return re.findall(r"[\w+#.-]+|[\u3400-\u9fff]+", text.lower())


def expand_query(text: str) -> str:
    additions = [english for chinese, english in ALIASES.items() if chinese in text]
    return " ".join([text, *additions])


def family_of(entry: dict) -> str:
    icon_id = entry["id"]
    for family in ("lucide", "tabler", "phosphor", "duotone", "fetched"):
        if icon_id.startswith(family + "-"):
            return family
    return "brand" if entry.get("category") == "brand" else "original"


def searchable(entry: dict) -> str:
    return " ".join(
        [
            entry.get("id", ""),
            entry.get("name", ""),
            " ".join(entry.get("tags", [])),
            entry.get("category", ""),
            entry.get("use_cases", ""),
        ]
    ).lower()


def score(entry: dict, query: str, tokens: list[str]) -> float:
    haystack = searchable(entry)
    icon_id = entry["id"].lower()
    name = entry.get("name", "").lower()
    tags = [tag.lower() for tag in entry.get("tags", [])]
    total = 0.0

    if query == icon_id or query == name:
        total += 140
    if query in icon_id or query in name:
        total += 42
    if query in haystack:
        total += 28

    for token in tokens:
        if token == icon_id:
            total += 55
        elif token in icon_id:
            total += 24
        if token == name:
            total += 38
        elif token in name:
            total += 18
        if token in tags:
            total += 30
        elif any(token in tag for tag in tags):
            total += 14
        if token in entry.get("use_cases", "").lower():
            total += 9

        candidates = [icon_id, name, *tags]
        total += 7 * max(
            (difflib.SequenceMatcher(None, token, candidate).ratio() for candidate in candidates),
            default=0,
        )

    # Prefer clean monochrome assets and the two most coherent paper families.
    if entry.get("recolorable"):
        total += 3
    if family_of(entry) in ("lucide", "tabler"):
        total += 2
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Concept to search for; English and common Chinese terms work")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument(
        "--family",
        choices=["original", "brand", "lucide", "tabler", "phosphor", "duotone", "fetched"],
    )
    parser.add_argument("--category")
    parser.add_argument("--recolorable", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    args = parser.parse_args()

    try:
        entries = json.loads(args.catalog.read_text(encoding="utf-8"))["icons"]
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        sys.exit(f"cannot read catalog {args.catalog}: {exc}")

    expanded = expand_query(args.query)
    query = expanded.lower().strip()
    tokens = tokenize(expanded)
    filtered = []
    for entry in entries:
        if args.family and family_of(entry) != args.family:
            continue
        if args.category and entry.get("category") != args.category:
            continue
        if args.recolorable and not entry.get("recolorable"):
            continue
        value = score(entry, query, tokens)
        if value > 4:
            filtered.append((value, entry))

    filtered.sort(key=lambda item: (-item[0], family_of(item[1]), item[1]["id"]))
    results = []
    for value, entry in filtered[: max(args.limit, 0)]:
        results.append(
            {
                "id": entry["id"],
                "name": entry.get("name", ""),
                "family": family_of(entry),
                "category": entry.get("category", ""),
                "recolorable": bool(entry.get("recolorable")),
                "score": round(value, 1),
                "use_cases": entry.get("use_cases", ""),
                "svg": entry.get("svg"),
            }
        )

    if args.as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    if not results:
        sys.exit("no matching icons; broaden the query or remove filters")
    for result in results:
        recolor = "recolor" if result["recolorable"] else "keep colors"
        print(
            f"{result['id']:<34} {result['family']:<10} "
            f"{recolor:<11} score={result['score']:>5.1f}  {result['use_cases']}"
        )


if __name__ == "__main__":
    main()
