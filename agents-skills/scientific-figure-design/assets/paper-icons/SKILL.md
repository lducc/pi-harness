---
name: paper-icons
description: Design publication-ready academic paper illustrations with a large vector icon library, semantic icon search, JSON-to-SVG composition, accessible paper palettes, SVG/PDF/PNG export, and deterministic figure validation. Use for method overviews, model architectures, data or agent pipelines, feedback loops, ablations, comparison diagrams, benchmark workflows, graphical abstracts, and icon-assisted figures for LaTeX, Word, slides, Mermaid, or draw.io.
---

# Paper Icons

Create a figure that communicates one research claim at its final printed size. Treat icons as semantic anchors, not decoration.

## Required workflow

1. **Write the figure sentence.** State what the reader must understand in one sentence. If that sentence is unclear, do not draw yet.
2. **Choose one visual grammar.** Read [references/figure-grammar.md](references/figure-grammar.md) and select the smallest archetype that expresses the claim.
3. **Set the publication geometry.** Default to `double` column (178 mm). Use `single` only for a genuinely simple figure. Keep body text readable after final scaling.
4. **Make a semantic inventory.** List entities, transformations, boundaries, evidence, and the meaning of every arrow. Remove anything that does not support the figure sentence.
5. **Select a restrained icon family.** Search the catalog; use at most one general icon family per figure. Prefer Lucide or Tabler stroke icons for technical diagrams and original silhouettes only when their visual weight matches.
6. **Compose editable SVG.** Prefer the bundled JSON composer for pipelines, grids, feedback loops, and small architectures. Hand-author SVG or use draw.io for irregular dense layouts.
7. **Validate and inspect.** Run deterministic checks, render a PNG, and visually inspect it at the intended paper width. Fix overlap, clipping, weak hierarchy, ambiguous arrows, and tiny text.
8. **Deliver sources.** Return the editable SVG, PDF, review PNG, JSON spec when used, and a short icon/source manifest.

Do not skip validation merely because the SVG renders.

## Choose the production path

### Structured figure: use the composer

Start from a template in `assets/templates/`:

```bash
SKILL=/absolute/path/to/paper-icons
cp "$SKILL/assets/templates/pipeline.json" ./method-overview.json
python3 "$SKILL/scripts/compose_figure.py" ./method-overview.json \
  --out ./method-overview.svg --pdf ./method-overview.pdf --png ./method-overview.png
python3 "$SKILL/scripts/validate_figure.py" ./method-overview.svg
```

Supported layouts:

- `pipeline`: horizontal or vertical stages
- `grid`: comparisons, ablations, or repeated modules
- `freeform`: explicit `x`, `y`, `w`, and `h` for architectures and loops

The composer inlines icons, embeds metadata, routes connectors behind nodes, wraps labels, exports vector PDF, and produces a review PNG. Read [references/spec-schema.md](references/spec-schema.md) before creating a spec from scratch.

### Irregular or dense figure: author SVG/draw.io

Use the same palette, typography, icon search, and quality gate. For draw.io, use absolute SVG paths during editing and embed icons as data URIs before final delivery if portability matters. Do not use raster icons in the final PDF when a vector source exists.

### Data-dominant figure

Use a plotting tool for quantitative marks. Use this skill only for consistent annotations, method glyphs, or small semantic callouts. Never replace a chart with icon decoration.

## Find icons semantically

Use `search_icons.py`; do not manually scan hundreds of filenames first.

```bash
python3 "$SKILL/scripts/search_icons.py" "vector database retrieval" --limit 8
python3 "$SKILL/scripts/search_icons.py" "模型训练" --family lucide --recolorable
python3 "$SKILL/scripts/search_icons.py" "closed model baseline" --category brand --json
```

Then visually confirm candidates in `library/overview/`. Search ranking is a shortlist, not a design decision.

Icon IDs are catalog keys such as `database`, `lucide-brain`, `tabler-database`, `phosphor-f-brain`, and `claude-color`. The catalog is `library/catalog.json`.

Selection rules:

- Match the concept, not the noun literally. A database icon means storage; it does not automatically mean “dataset.”
- Keep stroke/fill language consistent. Do not mix outline Lucide nodes with heavy silhouettes without a reason.
- Use one icon per node at most. Omit icons from secondary nodes when labels are clearer.
- Preserve official colors for `color_type: color` brand marks and use them only for academic identification.
- Prefer text over an unfamiliar pictogram. Icons must remain understandable without a legend.

## Recolor and export individual icons

```bash
python3 "$SKILL/scripts/recolor.py" lucide-brain --color 2563EB --out ./figure-assets
python3 "$SKILL/scripts/recolor.py" database --color navy --format both --size 512
```

Defaults: SVG + PNG, transparent background, exact paper accent. SVG output works without Python imaging packages. `rsvg-convert` is used when PNG/PDF output is requested.

Do not recolor entries with `recolorable: false`.

## Visual system

Use these defaults unless the paper already has a figure system:

- Canvas: white
- Text: `#172033`
- Muted text: `#5B6472`
- Accent: `#2563EB`
- Secondary: `#7C3AED`
- Success: `#15803D`
- Warning: `#B45309`
- Danger: `#B91C1C`
- Borders: `#CBD5E1`
- Typeface: `Arial, Helvetica, sans-serif`
- Node labels: approximately 8–9 pt at final size
- Captions: keep outside the SVG in the paper source

Use color to encode one stable variable. Preserve meaning across panels. Never rely on red/green alone; pair color with text, shape, or an icon.

## Figure quality gate

Run:

```bash
python3 "$SKILL/scripts/validate_figure.py" figure.svg
python3 "$SKILL/scripts/validate_figure.py" figure.svg --strict
```

Before delivery, confirm:

- The figure sentence is visible in a three-second scan.
- Reading order is unambiguous.
- Every arrow has a defined meaning and points to a valid target.
- Node labels use parallel grammar and avoid prose.
- Text remains readable at 85 mm or 178 mm, whichever is intended.
- No label, arrowhead, group boundary, or icon is clipped.
- The figure still works in grayscale and for common color-vision deficiencies.
- Panel labels match the manuscript references.
- SVG contains `<title>` and `<desc>` metadata.
- PDF is vector; PNG is only a review or slide fallback.

`validate_figure.py` catches structural problems, but visual inspection is still mandatory.

## Extend the library only when needed

If no existing icon fits, fetch a Lucide icon:

```bash
python3 "$SKILL/scripts/fetch_icon.py" gpu
python3 "$SKILL/scripts/make_overview.py"
```

Do not fetch a merely decorative substitute. When adding non-Lucide assets, record source and license in the catalog builder.

## Integration guidance

- **figure-designer:** use it to decide the research narrative; use this skill to realize the figure consistently.
- **Mermaid:** keep Mermaid for source-controlled logical diagrams; export and refine only when publication polish is required.
- **draw.io:** use for manual geometry and dense irregular routing; reuse this skill's icons and quality gate.
- **LaTeX:** include the generated PDF for robust vector output; use SVG only when the toolchain supports it reliably.
- **Slides:** use the PNG fallback only when the slide tool cannot preserve SVG.

Do not invoke multiple figure-authoring systems for the same artifact unless the user requests a comparison.
