# Scientific Figure Design

**Paper figures agents can author and humans can still edit.**

[中文说明](README.zh-CN.md) · [Examples](examples/README.md) ·
[Academic aesthetics](references/academic-aesthetics.md) ·
[Color system](references/paper-color-system.md)

Scientific Figure Design is an open agent skill and deterministic toolchain for
turning a research claim into an editable Draw.io figure, then exporting
publication-ready SVG, PDF, and 300 dpi PNG artifacts.

It addresses a practical failure mode of generative figure workflows: a raster
image may look plausible, but its labels, topology, geometry, and colors are
painful to revise and difficult to trust in a paper. Here, Draw.io is the
editable scene graph; SVG and PDF are the vector masters; PNG is only the review
preview.

![Editable kernel-agent figure](examples/kernel-agent-loop/preview.png)

## What is included

- A complete `scientific-figure-design` agent skill in [`SKILL.md`](SKILL.md).
- Claim-first Figure Contracts and reusable academic style tokens.
- A frozen paper-level palette contract with cross-figure drift checks.
- JSON-to-Draw.io generation with editable cards, connectors, labels, and
  embedded vector icons.
- A bundled catalog of **581 SVG icons**, with semantic search, recoloring,
  provenance, and validation.
- arXiv HTML figure collection and visual-corpus analysis.
- Strict checks for publication-size typography, strokes, palette use, icon
  consistency, unsafe SVG content, editability, and export quality.
- Real editable examples from
  [KerSor](https://github.com/qhy991/KerSor) and
  [Agents-Native-Engine](https://github.com/qhy991/Agents-Native-Engine).

## Artifact contract

```text
Research claim
  → Figure Contract
  → paper-wide palette
  → semantic icon search
  → structured figure spec
  → editable .drawio
  → strict validation
  → .svg + .pdf + 300 dpi .png
```

The `.drawio` file is the source of truth. The exported SVG/PDF remains vector
and suitable for LaTeX or Word. Every embedded icon is recorded in an adjacent
`.icons.json` manifest.

## Quick start

Requirements: Python 3.10+. The core builder and validators use only the Python
standard library.

```bash
git clone https://github.com/qhy991/Scientific-Figure-Design.git
cd Scientific-Figure-Design

cp assets/drawio-system-overview.json figure-spec.json
cp assets/paper-palette.yaml paper-palette.yaml

# Set paper_id, palette_id, role colors, and status=frozen before final figures.
python3 scripts/build_drawio_figure.py figure-spec.json \
  --paper-palette paper-palette.yaml \
  --out figure.drawio

python3 scripts/validate_drawio_figure.py figure.drawio \
  --paper-palette paper-palette.yaml --strict
```

The builder automatically uses the bundled icon catalog. Pass
`--paper-icons-skill /path/to/paper-icons` only to override it.

For export, install the Draw.io desktop CLI. Ghostscript is recommended for
physical-width PDF normalization:

```bash
python3 scripts/export_drawio_figure.py figure.drawio --mode preview
python3 scripts/export_drawio_figure.py figure.drawio \
  --mode final --formats svg,pdf,png
```

For a paper with several Draw.io figures:

```bash
python3 scripts/validate_paper_palette.py \
  --palette paper-palette.yaml figures/*.drawio --strict
```

## Install as an agent skill

Clone the repository directly into a supported skill directory:

```bash
git clone https://github.com/qhy991/Scientific-Figure-Design.git \
  ~/.agents/skills/scientific-figure-design
```

Then ask the agent to use `scientific-figure-design`. The skill supports four
operations:

1. mine figures and captions from arXiv HTML;
2. extract a paper or research area's visual language;
3. design and build an editable scientific figure;
4. redesign, export, or audit an existing figure set.

## Academic aesthetics are enforced

The visual policy is not a mood board. It is a publication constraint:

- design at 85 mm single-column or 178 mm double-column width;
- use 8–9 pt primary text, never below 7 pt;
- use no more than three visible type sizes and two font families;
- keep ordinary strokes around 0.8–1.4 pt;
- use three to five semantic hues plus neutrals;
- prohibit decorative gradients, glow, glass, bevels, and drop shadows;
- preserve one semantic mapping across Figure 1–N;
- require redundant cues for status instead of red/green alone;
- keep icons vector, source-recorded, and visually consistent.

Human-readable rules live in
[`references/academic-aesthetics.md`](references/academic-aesthetics.md);
machine-readable limits live in
[`assets/academic-style.yaml`](assets/academic-style.yaml).

## One paper, one color system

Copy [`assets/paper-palette.yaml`](assets/paper-palette.yaml) into the paper
project. Assign `ours`, recurring baselines, bounds, success, and failure once,
then freeze it. Every figure and plotting script should consume that same
mapping. The validators bind Draw.io sources to the palette ID and SHA-256 so
silent color drift becomes a build failure.

## Complete icon library

The bundled [`assets/paper-icons`](assets/paper-icons) catalog contains:

| Family | Count | License / status |
| --- | ---: | --- |
| Lucide | 177 | ISC |
| Tabler | 131 | MIT |
| Phosphor | 114 | MIT |
| Phosphor duotone | 51 | MIT |
| Lobe brand icons | 39 | MIT SVG code; trademarks remain protected |
| On-demand Lucide | 32 | ISC |
| Project-original academic icons | 37 | Repository MIT license |
| **Total** | **581** | |

Search the catalog:

```bash
python3 assets/paper-icons/scripts/search_icons.py \
  "retrieval database" --limit 8
```

Use at most one general icon family in a figure. Brand marks are for accurate
academic identification only: preserve official colors, do not imply
endorsement, and prefer a neutral text label when the logo is unnecessary.
See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and the machine-readable
[`license-manifest.json`](assets/paper-icons/library/license-manifest.json).

## arXiv figure mining

The collector prefers arXiv HTML because it preserves caption, subfigure, alt
text, source link, and document context:

```bash
python3 scripts/collect_arxiv_figures.py \
  --readme path/to/paper-list.md \
  --output-dir path/to/corpus \
  --workers 4
```

Install `requests` and `beautifulsoup4` for collection. Visual statistics and
contact sheets additionally use Pillow and CairoSVG:

```bash
python3 scripts/analyze_visuals.py \
  --root path/to/corpus \
  --output-dir path/to/corpus/analysis
```

## Examples

| Example | Editable source | Vector master | Design role |
| --- | --- | --- | --- |
| Kernel agent loop | [Draw.io](examples/kernel-agent-loop/figure.drawio) | [SVG](examples/kernel-agent-loop/figure.svg) | End-to-end generated pipeline |
| KerSor motivated example | [Draw.io](examples/kersor-motivated-example/figure.drawio) | [SVG](examples/kersor-motivated-example/figure.svg) | Before/after evidence transfer |
| KerSor control state | [Draw.io](examples/kersor-control-state/figure.drawio) | [SVG](examples/kersor-control-state/figure.svg) | Topology, control, and prior |
| Agent-native engine | [Draw.io](examples/agent-native-engine/figure.drawio) | [SVG](examples/agent-native-engine/figure.svg) | Problem framing and substrate |

Each example has a review PNG; most also include PDF. See
[`examples/README.md`](examples/README.md) for provenance and design notes.

## Development

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/*.py tests/*.py
ruff check scripts tests
```

Contributions are welcome. New icons must have a permissive source license and
machine-readable provenance. New figures should include editable source rather
than only a rendered image. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

Original work in this repository is released under the [MIT License](LICENSE).
Bundled third-party icons retain their upstream ISC/MIT licenses. Brand names
and logos remain trademarks of their respective owners.
