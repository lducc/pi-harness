---
name: scientific-figure-design
description: Mine figures from arXiv HTML and design, build, or redesign publication-ready scientific figures, including AI-agent self-evolution, co-evolution, memory, skill, tool, topology, and data-policy loops; paper-wide palette consistency; and an end-to-end paper-icons to editable Draw.io workflow with vector icon embedding, SVG/PDF/PNG export, and validation. Use for paper system overviews, method or architecture diagrams, agent and data pipelines, feedback loops, quantitative plots, rooflines, ablations, training curves, small multiples, worked examples, figure audits, caption drafting, visual-style or color-system extraction from related work, cross-figure palette audits, or requests to download and organize paper figures before analysis.
---

# Scientific Figure Design

Create scientific figures that make one research claim legible in five seconds
and remain editable, reproducible, and readable at publication size.

## Choose the operation

- **Mine a corpus**: download figures, captions, alt text, source URLs, and HTML
  context from arXiv papers. Follow [Corpus mining](#corpus-mining).
- **Design a new figure**: turn a claim, method, or result table into a figure.
  Follow [Figure workflow](#figure-workflow).
- **Produce an editable Draw.io figure**: combine a Figure Contract with
  `paper-icons`, generate `.drawio` XML, export, and validate. Follow
  [Icon-assisted Draw.io workflow](#icon-assisted-drawio-workflow).
- **Redesign or audit a figure**: inspect the source and final-size render, state
  the main communication failure, then enter the workflow at the earliest failed
  step.
- **Extract a visual language**: sample related figures, separate observed facts
  from visual inference, and summarize recurring composition, encoding, and
  failure patterns. Read `references/evidence-and-audit.md`.
- **Design an AI-agent evolution figure set**: make the mutable object, update
  signal, cadence, persistent state, acceptance gate, and longitudinal evidence
  explicit. Read `references/ai-agent-self-evolution.md`.

Read `references/visual-grammar.md` when choosing composition or encodings.
Read `references/academic-aesthetics.md` before designing, creating,
redesigning, or validating any final figure. It is a mandatory publication
constraint, not optional inspiration. `assets/academic-style.yaml` is the
machine-readable source of truth consumed by the Draw.io builder and validator;
read `references/paper-color-system.md` and create one project-local copy of
`assets/paper-palette.yaml` whenever designing or revising more than one figure
for the same paper. Freeze that contract before final Figure 1–N production.
Document any venue-specific exception in the Figure Contract before drawing.
The automatic strict gate never consumes those exceptions: it still reports the
violation. An exception becomes a waiver only after explicit human review and
approval; never treat a documented exception as silent machine authorization.
Read `references/tool-recipes.md` only for the tool family selected for the
artifact.
Read `references/drawio-production.md` before creating an icon-assisted Draw.io
artifact.

## Corpus mining

Prefer arXiv HTML because it preserves figure grouping, captions, subfigures,
alt text, and linked assets. Use PDF or source bundles only for papers without
usable HTML.

Run:

```bash
python scripts/collect_arxiv_figures.py \
  --readme path/to/paper-list.md \
  --output-dir path/to/corpus \
  --workers 4
```

For a single paper:

```bash
python scripts/collect_arxiv_figures.py \
  --id 2401.01234 \
  --output-dir path/to/corpus
```

For ar5iv fallback:

```bash
python scripts/collect_arxiv_figures.py \
  --id-file missing-ids.txt \
  --html-base-url https://ar5iv.labs.arxiv.org/html \
  --output-dir path/to/corpus/fallback/ar5iv
```

The collector requires `requests` and `beautifulsoup4`. Preserve `papers.json`,
`figures.jsonl`, `summary.json`, each paper's `manifest.json`, `source.html`,
and original assets. Do not claim full coverage until every requested paper has
either an HTML manifest or a documented PDF/source fallback.

To compute visual statistics and sampled contact sheets:

```bash
python scripts/analyze_visuals.py \
  --root path/to/corpus \
  --output-dir path/to/corpus/analysis
```

This script additionally requires `Pillow` and `cairosvg`. Treat caption-based
figure classes as review aids, not ground-truth content labels.

For an AI-agent or self-evolution corpus, add a caption-derived role audit:

```bash
python scripts/analyze_agent_figures.py \
  --root path/to/corpus \
  --output-dir path/to/corpus/analysis/agent-audit
```

Use its role gaps as manual-review questions. A caption can omit semantics that
are visible in the figure or explained in nearby prose, so never report these
tags as automatic scientific-quality scores.

## Figure workflow

### 1. Write the Figure Contract

Copy `assets/figure-contract.yaml` and complete it before drawing. Require:

- one-sentence claim;
- the five-second takeaway;
- audience and publication width;
- evidence and comparison objects;
- visual anchor such as a baseline, `1×`, diagonal, threshold, or theory limit;
- semantic encoding map;
- shared paper palette path, ID, status, and recurring method/baseline roles;
- data provenance;
- editable source and export formats.

For self-evolving or co-evolving agents, also complete `agent_evolution` in the
contract. Name every mutable object and frozen invariant; show the before/after
state, update signal and operator, cadence or timescale, persistent store,
acceptance and rejection paths, stability constraint, and evidence that the
internal state and task outcome improve across rounds. Do not use a circular
arrow as a substitute for these semantics.

Keep `academic_style.policy` pointed at `assets/academic-style.yaml`. Do not
weaken its typography, stroke, color, icon, or effects limits merely to make an
overcrowded figure pass; revise the structure. Put a justified, scoped
venue-specific deviation in `academic_style.exceptions`.
This field is an audit record, not validator input. `--strict` must still fail
the underlying rule; only an explicit human-reviewed waiver can approve the
deviation.

If the claim is ambiguous, propose the narrowest defensible claim and identify
the assumption. Do not use polish to hide missing evidence.

### 2. Select one archetype

- Method or control flow: system overview.
- Mechanism or transformation: worked example.
- Relative performance: point, bar, or paired comparison.
- Hardware headroom: roofline, SOL, or measured-vs-bound scatter.
- Generalization: aligned small multiples.
- Component contribution: ablation.
- Failure composition: taxonomy with stacked bars or heatmap.
- Optimization dynamics: aligned training/search curves.
- Agent self-evolution: a bounded single loop, dual-timescale loop,
  search/topology graph, role cycle, or persistent-memory flow. Select the
  topology from `references/ai-agent-self-evolution.md`, not from decorative
  preference.

One figure gets one primary claim. Use panels for supporting claims without
introducing unrelated visual grammars.

### 3. Build a grayscale skeleton

Lay out the canvas, panel grid, hierarchy, main path, axes, and anchors without
decorative color. Check:

- reading order is unambiguous;
- the innovation or decisive comparison is visually dominant;
- arrows cross rarely and feedback loops occupy one bounded area;
- axes and panel ranges support the intended comparison;
- labels remain readable at final width.

If the figure fails in grayscale, revise structure before adding color.

### 4. Add semantic encodings

Use color for stable meaning, not decoration. Start from
`assets/academic-style.yaml`; `assets/style-tokens.json` is a convenient
human-facing projection of the same defaults. Adapt to the paper's existing
visual language only within the academic limits or through a documented
exception and explicit human waiver.

For multi-figure work, copy `assets/paper-palette.yaml` into the paper project
and use it as the single color source of truth. Set a stable `paper_id`, assign
`ours`, recurring baselines, bounds, success, and failure once, then freeze the
contract. Every figure and plotting script must consume the same mapping.

- neutral gray: baselines, context, inactive structure;
- blue/cyan: input, data, infrastructure, normal path;
- purple: model, agent, generative module;
- orange/yellow: optimization, search, candidate;
- green: verified success or improvement;
- red: failure, invalidity, regression.

Use three to five semantic colors plus neutrals. Keep the mapping consistent
across the paper. Add shape, line style, or direct labels when grayscale or
color-vision compatibility requires redundancy.

Never rotate palette order between plots, recolor `ours` between diagrams and
charts, or use the same color for a method in one figure and a status in
another. Read `references/paper-color-system.md` for chart-role and existing
manuscript rules.

### 5. Implement with the right tool

- Use Matplotlib/Seaborn for numeric plots, small multiples, rooflines,
  ablations, uncertainty, and heatmaps.
- Use Graphviz or Mermaid for simple DAGs and dependency flows.
- Use the bundled Draw.io bridge plus `paper-icons` for editable, icon-assisted
  system overviews, architectures, and feedback loops.
- Use editable SVG, Draw.io, Figma, or presentation software for irregular
  manually composed system overviews.
- Use TikZ/PGF when exact LaTeX typography or formula alignment is central.
- Generate repeated panels with code; do not hand-align dozens of plots.

Do not use generative image tools for final figures containing exact numbers,
code, axes, formulas, or topology. They may be used only for early concept
exploration or non-data illustration.

## Icon-assisted Draw.io workflow

Use this path when the final artifact must be editable in Draw.io or the figure
needs semantic vector icons.

### 1. Design before selecting icons

Complete the Figure Contract and semantic inventory. Define entities,
transformations, states, boundaries, evidence, and arrow meanings. Select the
archetype and reading order before searching for icons.

Use icons as semantic anchors. Keep one general family, normally Lucide or
Tabler, and at most one icon per node. Prefer a clear label when an icon would
be unfamiliar or decorative.

### 2. Search the bundled paper-icons catalog

Use `assets/paper-icons/scripts/search_icons.py` with semantic queries and
family filters. The bundled catalog contains 581 SVG icons and is the default
used by the Draw.io bridge. A user-installed `paper-icons` skill or an explicit
`--paper-icons-skill` path may override it. Visually confirm the shortlist. Do
not infer an icon from its filename alone, mix outline and filled families
casually, recolor protected brand marks, or replace quantitative evidence with
pictograms.

Before adding or publishing an icon, verify its entry in
`assets/paper-icons/library/catalog.json` and its license group in
`assets/paper-icons/library/license-manifest.json`. General Lucide, Tabler, and
Phosphor marks may be recolored by the paper palette. Brand marks are only for
accurate academic identification: preserve official colors, do not imply
endorsement, and prefer neutral text when the logo is unnecessary.

### 3. Build from one shared spec

Copy `assets/drawio-system-overview.json`, then edit its metadata, nodes, edges,
groups, annotations, and layout. Build:

```bash
python3 scripts/build_drawio_figure.py figure-spec.json \
  --paper-palette paper-palette.yaml \
  --out figure.drawio
```

The bridge embeds paper-icons SVGs as vector data URIs, preserves editable
Draw.io cards and connectors, distributes connection ports, and writes an icon
source manifest. Pass `--paper-icons-skill /absolute/path/to/paper-icons` only
when intentionally overriding the bundled catalog.

Validate before export:

```bash
python3 scripts/validate_drawio_figure.py figure.drawio \
  --paper-palette paper-palette.yaml --strict
```

Strict validation applies `assets/academic-style.yaml`: final-size typography,
font-family count, line weight, semantic hue count, icon family and scale,
forbidden effects, geometry, embedded SVG safety, and source metadata. A
warning fails the strict gate. When the source binds a paper palette, strict
validation also verifies the palette ID and SHA-256; passing no palette file is
a failed unverified-binding warning.

### 4. Export a clean preview and inspect it

```bash
python3 scripts/export_drawio_figure.py figure.drawio --mode preview
```

Inspect the PNG visually at final width. Fix overlap, clipping, weak hierarchy,
ambiguous arrows, inconsistent icons, and tiny text. Regenerate from the spec
for topology or layout changes; patch the existing `.drawio` XML for isolated
label, color, position, or size changes.

If the draw.io CLI exists but fails because of macOS sandbox isolation, retry
once outside the sandbox. If unavailable, return the valid `.drawio` XML and use
the browser fallback described by `drawio-skill`.

### 5. Export approved masters

```bash
python3 scripts/export_drawio_figure.py figure.drawio \
  --mode final --formats svg,pdf,png
```

Final exports use a zero external border. The generated canvas boundary keeps
the SVG viewBox aligned with source geometry; the exporter enforces at least
300 dpi for PNG and normalizes the PDF to the declared physical width when
Ghostscript is available.

Run both quality gates:

```bash
python3 scripts/validate_drawio_figure.py figure.drawio \
  --paper-palette paper-palette.yaml --strict
python3 assets/paper-icons/scripts/validate_figure.py figure.svg
```

For a manuscript with multiple Draw.io figures, run the cross-figure gate:

```bash
python3 scripts/validate_paper_palette.py \
  --palette paper-palette.yaml figures/*.drawio --strict
```

Open the final PNG with vision and inspect the exported SVG/PDF. The final
exporter embeds Draw.io editability, repairs embedded PNG endings when needed,
and adds accessible SVG metadata and physical paper width.

### 6. Add explanatory anchors

Make the conclusion discoverable before the legend:

- draw and label the baseline or theory bound;
- directly label the decisive method or point when space allows;
- annotate collapse, plateau, phase change, or headroom;
- include uncertainty and sample definition where relevant;
- order categories by the comparison the reader should make.

Prefer direct labels over a distant legend. Remove ink that does not support
the claim.

### 7. Validate at publication size

Export an editable source plus SVG or PDF and a PNG preview. Validate:

- single-column width near 85 mm and double-column width near 178 mm;
- final text at least 7 pt, preferably 8–9 pt for primary labels;
- no more than three visible type sizes and one primary sans-serif family;
- strokes around 0.8–1.4 pt, with emphasis never above 1.6 pt by default;
- no more than five semantic hues and no decorative effects;
- one frozen paper palette binds every manuscript figure; recurring methods,
  baselines, status colors, and bounds do not drift;
- no clipped labels, rasterized text, hidden data, or overlapping legends;
- grayscale and common color-vision conditions preserve distinctions;
- PNG preview is at least 300 dpi when raster output is required.
- final exports use border 0 and retain the generated full-page canvas boundary.

Render the actual exported artifact and inspect it. Do not treat successful
source execution as visual verification.

### 8. Run two communication tests

- **Five-second test**: can a reader state the takeaway, comparison, and
  good/bad direction?
- **Caption test**: without the paper body, does the caption define conditions,
  metrics, baselines, uncertainty, and conclusion?

If either fails, revise the figure rather than lengthening the caption to
compensate for a broken visual hierarchy.

## Archetype-specific requirements

### System overview

Use a left-to-right structure such as input → core generation/search/training →
execution/verification/feedback. Group stages in light containers. Put concrete
artifacts—code, kernel, profile, test result—inside the flow. Confine iteration
to a clear loop and make the novel stage dominant.

For an evolving agent, label the state transition explicitly, such as
`S_t → candidate S_{t+1} → verified S_{t+1}`. Distinguish inference-time,
per-task, per-batch, and slower outer-loop updates through lane boundaries,
cadence labels, or line styles. Draw persistent stores as stateful artifacts,
not generic process boxes; show the write gate and the next-round read path.
Keep frozen backbones or environment invariants neutral. Use the agent-evolution
reference for the full visual and evidence checklist.

### Quantitative comparison

Choose a chart from the analytical question, not from habit. Use consistent
scales for intended cross-panel comparisons. Show a labeled anchor and use
direct values sparingly. Avoid truncated axes unless the figure makes the
truncation unmistakable and the comparison remains honest.

### Ablation and training curves

Compare the full method with two to five meaningful removals or interventions.
Show uncertainty when available. Separate reward, entropy, gradient norm, and
clip ratio into aligned panels. Annotate the event that explains the conclusion,
not every local fluctuation.

### Worked example

Use source/problem → intermediate representation/transformation → generated
artifact/result. Show only the 5–15 relevant code lines. Align corresponding
variables or tensor tiles with stable colors and number the transformation
steps.

## Deliverables

Unless the user requests otherwise, provide:

1. completed Figure Contract;
2. editable source, including `.drawio` when that production path is selected;
3. icon/source manifest for icon-assisted figures;
4. SVG and PDF masters;
5. final-size PNG preview;
6. concise caption;
7. provenance note for data and externally sourced visual elements;
8. a short validation record covering structure, size, grayscale, and
   five-second tests;
9. one frozen `paper-palette.yaml` plus a zero-drift cross-figure audit for
   multi-figure manuscript work.

When only advising, provide the Figure Contract, a wireframe, encoding map, and
specific revision list instead of pretending a final artifact was created.
