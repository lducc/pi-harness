#!/usr/bin/env python3
"""Collect figures and captions from arXiv HTML papers.

The collector intentionally uses arXiv's HTML representation instead of parsing
PDF pages. It preserves figure grouping, subfigure order, captions, alt text,
source URLs, and local file names in a machine-readable manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

ARXIV_URL_RE = re.compile(
    r"https?://(?:www\.)?arxiv\.org/(?:abs|html|pdf)/"
    r"(?P<id>\d{4}\.\d{4,5})(?:v\d+)?"
)
MARKDOWN_PAPER_RE = re.compile(
    r"\[\*\*(?P<title>.+?)\*\*\]\("
    r"https?://(?:www\.)?arxiv\.org/(?:abs|html|pdf)/"
    r"(?P<id>\d{4}\.\d{4,5})(?:v\d+)?\)"
)
SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")

USER_AGENT = (
    "scientific-figure-design/1.0 "
    "(non-commercial research figure analysis; contact: local-codex-user)"
)


@dataclass
class ImageRecord:
    image_index: int
    asset_kind: str
    source_url: str
    local_path: str | None
    alt_text: str
    subfigure_label: str | None
    subfigure_caption: str | None
    width_hint: str | None
    height_hint: str | None
    sha256: str | None
    status: str
    error: str | None = None


@dataclass
class FigureRecord:
    figure_index: int
    figure_id: str | None
    caption: str
    label: str | None
    figure_type: str
    images: list[ImageRecord]


def normalize_ws(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def safe_name(value: str) -> str:
    cleaned = SAFE_NAME_RE.sub("-", value.strip()).strip("-")
    return cleaned[:120] or "item"


def infer_extension(url: str, content_type: str | None) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix and len(suffix) <= 8:
        return suffix
    guessed = mimetypes.guess_extension((content_type or "").split(";")[0].strip())
    return guessed or ".bin"


def classify_figure(caption: str) -> str:
    text = caption.lower()
    rules: list[tuple[str, tuple[str, ...]]] = [
        ("ablation", ("ablation",)),
        ("roofline", ("roofline", "speed-of-light", " sol ")),
        ("heatmap", ("heatmap",)),
        ("scaling", ("scalability", "scaling", "scale with")),
        (
            "system-overview",
            (
                "overview",
                "architecture",
                "framework",
                "workflow",
                "pipeline",
                "system design",
            ),
        ),
        (
            "quantitative-comparison",
            (
                "performance",
                "speedup",
                "latency",
                "throughput",
                "accuracy",
                "benchmark",
                "comparison",
                "pass rate",
                "success rate",
            ),
        ),
        (
            "training-process",
            (
                "training",
                "reinforcement learning",
                "reward",
                "fine-tuning",
                "optimization process",
            ),
        ),
        (
            "dataset-or-taxonomy",
            (
                "dataset",
                "distribution",
                "taxonomy",
                "categories",
                "breakdown",
                "failure modes",
            ),
        ),
        (
            "worked-example",
            ("example", "case study", "illustration", "demonstration"),
        ),
    ]
    for label, needles in rules:
        if any(needle in text for needle in needles):
            return label
    return "other"


def parse_readme(path: Path) -> tuple[list[str], dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    ids = sorted({match.group("id") for match in ARXIV_URL_RE.finditer(text)})
    titles: dict[str, str] = {}
    for match in MARKDOWN_PAPER_RE.finditer(text):
        titles.setdefault(match.group("id"), normalize_ws(match.group("title")))
    return ids, titles


def load_ids(args: argparse.Namespace) -> tuple[list[str], dict[str, str]]:
    titles: dict[str, str] = {}
    ids: list[str] = []
    if args.readme:
        ids, titles = parse_readme(args.readme)
    if args.id:
        ids.extend(item.split("v", 1)[0] for item in args.id)
    if args.id_file:
        ids.extend(
            line.strip().split("v", 1)[0]
            for line in args.id_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    unique = list(dict.fromkeys(ids))
    if args.limit is not None:
        unique = unique[: args.limit]
    return unique, titles


def request_with_retries(
    session: requests.Session,
    url: str,
    *,
    timeout: float,
    retries: int,
    stream: bool = False,
) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = session.get(url, timeout=timeout, stream=stream)
            if response.status_code == 429 or response.status_code >= 500:
                response.close()
                raise requests.HTTPError(f"HTTP {response.status_code}")
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt == retries:
                break
            time.sleep(min(8.0, 1.0 * 2**attempt))
    raise RuntimeError(f"request failed for {url}: {last_error}")


def download_image(
    session: requests.Session,
    *,
    source_url: str,
    destination_stem: Path,
    timeout: float,
    retries: int,
) -> tuple[Path, str]:
    response = request_with_retries(
        session,
        source_url,
        timeout=timeout,
        retries=retries,
        stream=True,
    )
    response.raise_for_status()
    extension = infer_extension(source_url, response.headers.get("content-type"))
    destination = destination_stem.with_suffix(extension)
    digest = hashlib.sha256()
    with destination.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=1024 * 128):
            if chunk:
                digest.update(chunk)
                handle.write(chunk)
    response.close()
    return destination, digest.hexdigest()


def figure_nodes(soup: BeautifulSoup) -> Iterable:
    candidates = [
        node
        for node in soup.select("figure.ltx_figure")
        if node.find_parent("figure", class_="ltx_figure") is None
    ]
    if candidates:
        return [
            node
            for node in candidates
            if node.find("img") is not None
            or node.select_one("svg.ltx_picture") is not None
            or (label_from_caption(direct_caption(node)) or "").lower().startswith(
                "figure"
            )
        ]
    return [
        node
        for node in soup.find_all("figure")
        if node.find_parent("figure") is None
    ]


def direct_caption(node):
    caption = node.find("figcaption", recursive=False)
    if caption is None:
        caption = node.find(class_="ltx_caption", recursive=False)
    if caption is None:
        caption = node.select_one("figcaption, .ltx_caption")
    return caption


def label_from_caption(caption_node) -> str | None:
    if caption_node is None:
        return None
    label_node = caption_node.select_one(".ltx_tag_figure, .ltx_tag")
    if label_node is None:
        return None
    return normalize_ws(label_node.get_text(" ", strip=True)) or None


def extract_title(soup: BeautifulSoup, fallback: str) -> str:
    for selector in (
        "h1.ltx_title_document",
        "h1.title",
        "meta[name='citation_title']",
        "title",
    ):
        node = soup.select_one(selector)
        if node is None:
            continue
        value = node.get("content") if node.name == "meta" else node.get_text(" ")
        value = normalize_ws(value)
        if value:
            return value
    return fallback


def collect_paper(
    session: requests.Session,
    *,
    arxiv_id: str,
    fallback_title: str,
    output_dir: Path,
    timeout: float,
    retries: int,
    max_figures: int | None,
    overwrite: bool,
    html_base_url: str,
) -> dict:
    paper_dir = output_dir / "papers" / arxiv_id
    image_dir = paper_dir / "images"
    manifest_path = paper_dir / "manifest.json"
    if manifest_path.exists() and not overwrite:
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    paper_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    html_url = f"{html_base_url.rstrip('/')}/{arxiv_id}"
    record: dict = {
        "arxiv_id": arxiv_id,
        "html_url": html_url,
        "title": fallback_title or arxiv_id,
        "status": "pending",
        "http_status": None,
        "resolved_html_url": None,
        "html_sha256": None,
        "html_local_path": None,
        "figures": [],
        "error": None,
    }
    try:
        response = request_with_retries(
            session,
            html_url,
            timeout=timeout,
            retries=retries,
        )
        record["http_status"] = response.status_code
        record["resolved_html_url"] = response.url
        if response.status_code != 200:
            record["status"] = "html-unavailable"
            record["error"] = f"HTTP {response.status_code}"
            response.close()
            manifest_path.write_text(
                json.dumps(record, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return record
        html_content = response.content
        response.close()
        html_path = paper_dir / "source.html"
        html_path.write_bytes(html_content)
        record["html_sha256"] = hashlib.sha256(html_content).hexdigest()
        record["html_local_path"] = str(html_path.relative_to(output_dir))
        soup = BeautifulSoup(html_content, "html.parser")
        base_node = soup.select_one("base[href]")
        if base_node is not None:
            asset_base_url = urljoin(
                record["resolved_html_url"],
                base_node.get("href"),
            )
        else:
            asset_base_url = urljoin(record["resolved_html_url"], "./")
        record["title"] = extract_title(soup, record["title"])
        nodes = list(figure_nodes(soup))
        if max_figures is not None:
            nodes = nodes[:max_figures]
        figures: list[dict] = []
        for figure_index, node in enumerate(nodes, start=1):
            caption_node = direct_caption(node)
            caption = normalize_ws(
                caption_node.get_text(" ", strip=True) if caption_node else ""
            )
            label = label_from_caption(caption_node)
            images: list[ImageRecord] = []
            assets = [
                asset
                for asset in node.find_all(["img", "svg"])
                if asset.name == "img"
                or "ltx_picture" in (asset.get("class") or [])
            ]
            for image_index, image in enumerate(assets, start=1):
                image_parent_figure = image.find_parent("figure")
                subfigure_caption_node = None
                if image_parent_figure is not None and image_parent_figure is not node:
                    subfigure_caption_node = direct_caption(image_parent_figure)
                subfigure_caption = (
                    normalize_ws(
                        subfigure_caption_node.get_text(" ", strip=True)
                        if subfigure_caption_node
                        else ""
                    )
                    or None
                )
                subfigure_label = label_from_caption(subfigure_caption_node)
                stem = image_dir / f"figure-{figure_index:02d}-{image_index:02d}"
                if image.name == "svg":
                    svg_id = image.get("id") or f"inline-svg-{image_index}"
                    source_url = f"{record['resolved_html_url']}#{svg_id}"
                    destination = stem.with_suffix(".svg")
                    image["xmlns"] = image.get("xmlns") or "http://www.w3.org/2000/svg"
                    content = str(image).encode("utf-8")
                    destination.write_bytes(content)
                    image_record = ImageRecord(
                        image_index=image_index,
                        asset_kind="inline-svg",
                        source_url=source_url,
                        local_path=str(destination.relative_to(output_dir)),
                        alt_text=normalize_ws(
                            image.get("aria-label") or image.get("title")
                        ),
                        subfigure_label=subfigure_label,
                        subfigure_caption=subfigure_caption,
                        width_hint=image.get("width"),
                        height_hint=image.get("height"),
                        sha256=hashlib.sha256(content).hexdigest(),
                        status="extracted",
                    )
                else:
                    raw_src = image.get("src") or image.get("data-src")
                    if not raw_src or raw_src.startswith("data:"):
                        continue
                    source_url = urljoin(asset_base_url, raw_src)
                    try:
                        destination, sha256 = download_image(
                            session,
                            source_url=source_url,
                            destination_stem=stem,
                            timeout=timeout,
                            retries=retries,
                        )
                        image_record = ImageRecord(
                            image_index=image_index,
                            asset_kind="linked-image",
                            source_url=source_url,
                            local_path=str(destination.relative_to(output_dir)),
                            alt_text=normalize_ws(image.get("alt")),
                            subfigure_label=subfigure_label,
                            subfigure_caption=subfigure_caption,
                            width_hint=image.get("width"),
                            height_hint=image.get("height"),
                            sha256=sha256,
                            status="downloaded",
                        )
                    except Exception as exc:  # keep the paper-level crawl moving
                        image_record = ImageRecord(
                            image_index=image_index,
                            asset_kind="linked-image",
                            source_url=source_url,
                            local_path=None,
                            alt_text=normalize_ws(image.get("alt")),
                            subfigure_label=subfigure_label,
                            subfigure_caption=subfigure_caption,
                            width_hint=image.get("width"),
                            height_hint=image.get("height"),
                            sha256=None,
                            status="download-error",
                            error=str(exc),
                        )
                images.append(image_record)
            figure = FigureRecord(
                figure_index=figure_index,
                figure_id=node.get("id"),
                caption=caption,
                label=label,
                figure_type=classify_figure(caption),
                images=images,
            )
            figures.append(asdict(figure))
        record["figures"] = figures
        record["status"] = "ok" if figures else "html-no-figures"
    except Exception as exc:
        record["status"] = "request-error"
        record["error"] = str(exc)

    manifest_path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return record


def write_aggregate(output_dir: Path, papers: list[dict]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    all_figures: list[dict] = []
    statuses: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    image_count = 0
    downloaded_count = 0
    for paper in papers:
        statuses[paper["status"]] = statuses.get(paper["status"], 0) + 1
        for figure in paper.get("figures", []):
            flattened = {
                "arxiv_id": paper["arxiv_id"],
                "paper_title": paper["title"],
                "html_url": paper["html_url"],
                **figure,
            }
            all_figures.append(flattened)
            figure_type = figure["figure_type"]
            type_counts[figure_type] = type_counts.get(figure_type, 0) + 1
            image_count += len(figure["images"])
            downloaded_count += sum(
                image["status"] in {"downloaded", "extracted"}
                for image in figure["images"]
            )

    (output_dir / "papers.json").write_text(
        json.dumps(papers, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with (output_dir / "figures.jsonl").open("w", encoding="utf-8") as handle:
        for figure in all_figures:
            handle.write(json.dumps(figure, ensure_ascii=False) + "\n")
    summary = {
        "paper_count": len(papers),
        "paper_statuses": dict(sorted(statuses.items())),
        "figure_count": len(all_figures),
        "image_count": image_count,
        "downloaded_image_count": downloaded_count,
        "figure_type_counts": dict(
            sorted(type_counts.items(), key=lambda item: (-item[1], item[0]))
        ),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--readme",
        type=Path,
        help="Markdown file containing arXiv paper links.",
    )
    parser.add_argument(
        "--id",
        action="append",
        help="Single arXiv ID; repeat to collect several papers.",
    )
    parser.add_argument(
        "--id-file",
        type=Path,
        help="Text file containing one arXiv ID per line.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--max-figures", type=int)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--delay", type=float, default=0.4)
    parser.add_argument(
        "--html-base-url",
        default="https://arxiv.org/html",
        help="HTML service base URL; use ar5iv as a fallback when needed.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of papers to collect concurrently (recommended maximum: 4).",
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ids, titles = load_ids(args)
    if not ids:
        raise SystemExit("No arXiv IDs found. Pass --readme and/or --id.")
    if args.workers < 1:
        raise SystemExit("--workers must be at least 1.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    papers: list[dict] = []
    total = len(ids)

    def collect_one(arxiv_id: str, stagger: float = 0.0) -> dict:
        if stagger:
            time.sleep(stagger)
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        try:
            return collect_paper(
                session,
                arxiv_id=arxiv_id,
                fallback_title=titles.get(arxiv_id, ""),
                output_dir=args.output_dir,
                timeout=args.timeout,
                retries=args.retries,
                max_figures=args.max_figures,
                overwrite=args.overwrite,
                html_base_url=args.html_base_url,
            )
        finally:
            session.close()

    if args.workers == 1:
        for index, arxiv_id in enumerate(ids, start=1):
            print(f"[{index:03d}/{total:03d}] {arxiv_id}", flush=True)
            papers.append(collect_one(arxiv_id))
            if index != total:
                time.sleep(args.delay)
    else:
        completed = 0
        by_id: dict[str, dict] = {}
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(
                    collect_one,
                    arxiv_id,
                    (index % args.workers) * args.delay,
                ): arxiv_id
                for index, arxiv_id in enumerate(ids)
            }
            for future in as_completed(futures):
                arxiv_id = futures[future]
                by_id[arxiv_id] = future.result()
                completed += 1
                print(
                    f"[{completed:03d}/{total:03d}] {arxiv_id} "
                    f"{by_id[arxiv_id]['status']}",
                    flush=True,
                )
        papers = [by_id[arxiv_id] for arxiv_id in ids]
    write_aggregate(args.output_dir, papers)
    print(json.dumps(json.loads((args.output_dir / "summary.json").read_text())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
