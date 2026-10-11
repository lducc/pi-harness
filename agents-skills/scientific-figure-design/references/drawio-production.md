# Icon-assisted Draw.io production

Use this reference for method overviews, architecture diagrams, feedback loops,
worked examples, or other figures whose final editable source should be
`.drawio`.

## Production contract

Treat the tools as one pipeline with distinct responsibilities:

1. `scientific-figure-design`: define the claim, archetype, semantic inventory,
   visual anchor, and validation criteria.
2. `references/academic-aesthetics.md` and `assets/academic-style.yaml`: impose
   the publication geometry, typography, stroke, color, icon, and effects
   constraints.
3. `references/paper-color-system.md` and `assets/paper-palette.yaml`: freeze
   one semantic palette for every figure in the manuscript.
4. `paper-icons`: search and select a coherent vector icon family.
5. `build_drawio_figure.py`: turn the shared JSON spec into editable draw.io
   geometry with embedded vector icons.
6. draw.io desktop: render preview and final SVG/PDF/PNG.
7. deterministic validators plus visual inspection: reject structural and
   communication failures.

Do not begin with icon selection. Icons cannot repair an unclear scientific
claim or topology.

## 1. Complete the Figure Contract

Fill `assets/figure-contract.yaml`. Set `icon_system.enabled` and
`drawio.enabled` to true. Keep `academic_style.policy` unchanged unless the
venue is stricter; document any scoped exception with a reason. Write the
semantic inventory before searching:

Copy `assets/paper-palette.yaml` into the paper project. Set `paper_id`, assign
stable method/baseline/status roles, and freeze it before final Figure 1–N
production. Every figure in the paper must bind to this same file.

`academic_style.exceptions` is not an automatic bypass. The strict validator
does not consume it and continues to report the violation. A deviation requires
an explicit, scoped human-reviewed waiver before publication.

- entities;
- transformations;
- states;
- execution or ownership boundaries;
- evidence;
- relations and the meaning of every arrow.

Choose one icon family. Default to Lucide or Tabler outline icons. Use brand
marks only to identify an actual external model, framework, or hardware vendor.
Combining a brand family with a general icon family is still two families:
automatic strict validation enforces the total family limit of one. Such a mix
requires a documented exception plus an explicit human-reviewed waiver; it
never passes the automatic gate silently.

## 2. Search paper-icons

Locate the user's installed `paper-icons` skill, then search semantically:

```bash
python3 /absolute/path/to/paper-icons/scripts/search_icons.py \
  "LLM agent generation" --family lucide --recolorable --json

python3 /absolute/path/to/paper-icons/scripts/search_icons.py \
  "GPU execution benchmark" --family lucide --recolorable --json
```

Confirm candidates visually in `paper-icons/library/overview/`. Search ranking
is only a shortlist. Use at most one icon per semantic node and omit icons when
the label communicates faster.

## 3. Write the shared JSON spec

Start from `assets/drawio-system-overview.json`. The bridge accepts the core
`paper-icons` schema:

- `metadata.title`, `metadata.description`, and `metadata.claim`;
- `paper_palette.path`: shared palette path, resolved relative to the spec;
- `figure.column`: `single` or `double`;
- `figure.layout`: `pipeline`, `grid`, or `freeform`;
- `figure.direction`: `horizontal` or `vertical`;
- `nodes`: `id`, `label`, optional `subtitle`, `icon`, `tone`, `shape`, `badge`,
  `kind`, `group`, and geometry;
- `edges`: `from`, `to`, optional `label`, `tone`, `style`, `route`, `arrow`,
  `entry`, `exit`, `points`, and `relation`;
- optional `groups` and `annotations`.

For `freeform`, every node requires `x`, `y`, `w`, and `h`. Coordinates use the
draw.io canvas. Default canvases are `1080 × 480` for double column and
`560 × 420` for single column.

Use these tones: `neutral`, `accent`, `secondary`, `success`, `warning`,
`danger`. Use these shapes: `round`, `rect`, `pill`, `database`, `circle`.

## 4. Generate editable Draw.io XML

```bash
python3 scripts/build_drawio_figure.py figure-spec.json \
  --paper-palette paper-palette.yaml \
  --out figure.drawio \
  --paper-icons-skill /absolute/path/to/paper-icons

python3 scripts/validate_drawio_figure.py figure.drawio \
  --paper-palette paper-palette.yaml --strict
```

The builder:

- creates editable containers, labels, badges, groups, and connectors;
- creates a full-page white canvas boundary so source typography and final-size
  typography use the same scale;
- reads `assets/academic-style.yaml` and writes its version, final paper width,
  minimum text size, semantic hues, and icon families into source metadata;
- binds the paper palette ID, schema, status, and canonical SHA-256 to the
  Draw.io source and rejects per-figure color drift;
- distributes connector ports to reduce stacked edges;
- embeds selected paper-icons SVGs as self-contained data URIs;
- recolors only catalog entries marked `recolorable`;
- writes `figure.icons.json` with icon IDs, sources, applied colors, and the
  SHA-256 of every decoded embedded SVG payload;
- stores title, description, claim, paper width, and semantic metadata in the
  draw.io source.

Do not replace embedded SVG icons with screenshots or raster PNGs.

## 5. Export and inspect the draft

The draw.io desktop CLI may require execution outside a macOS application
sandbox. First generate a clean preview without embedded diagram XML:

```bash
python3 scripts/export_drawio_figure.py figure.drawio \
  --mode preview --output-dir .
```

Inspect `figure.png` at its intended paper width. Check reading order, clipping,
arrow routing, label parallelism, icon consistency, and visual dominance. Make
targeted edits to the JSON spec or `.drawio` XML, regenerate or patch, and
repeat for at most two automatic self-check rounds before showing the user.

If the CLI binary exists but fails because of Electron, display, or sandbox
isolation, retry once outside the sandbox. If it is genuinely unavailable,
deliver the valid `.drawio` XML and use the browser fallback from `drawio-skill`
rather than inventing a raster substitute.

## 6. Produce final deliverables

After approval:

```bash
python3 scripts/export_drawio_figure.py figure.drawio \
  --mode final --formats svg,pdf,png --output-dir .

python3 scripts/validate_drawio_figure.py figure.drawio \
  --paper-palette paper-palette.yaml --strict
python3 /absolute/path/to/paper-icons/scripts/validate_figure.py figure.svg

python3 scripts/validate_paper_palette.py \
  --palette paper-palette.yaml figures/*.drawio --strict
```

The strict validator rejects invalid embedded SVG, payload/manifest hash
mismatches, bad edge endpoints, missing or empty relation metadata, hidden or
partially transparent text, missing style metadata, and geometry errors. It
treats academic-aesthetic violations
as warnings, which also fail under `--strict`: sub-7 pt text, more than three
type sizes, mixed primary fonts, illegible strokes, more than five semantic
hues, multiple icon families, out-of-scale icons, gradients, shadows, glass,
comic/sketch/3D styling, and animated connectors.

When a paper palette is bound, strict validation also requires the supplied
palette contract, verifies its ID and SHA-256, and rejects undeclared semantic
colors. The paper-level validator requires a frozen palette and non-empty
`paper_id` when auditing multiple figures.

The final exporter:

- uses `-e` for SVG/PDF/PNG so draw.io editability is embedded;
- requires zero external border for final masters and verifies the SVG viewBox
  against the Draw.io canvas;
- writes `figure.drawio.png` for the embedded final PNG;
- repairs the known truncated PNG IEND emitted by some draw.io versions;
- enforces at least 300 dpi at the declared paper width;
- normalizes the PDF page to the declared physical width with Ghostscript while
  retaining vector content and Draw.io metadata; a requested final PDF fails
  explicitly when Ghostscript is unavailable because the declared physical
  width cannot be guaranteed;
- injects accessible `<title>` and `<desc>` metadata into SVG;
- sets the SVG physical width to 85 mm or 178 mm from the figure spec.

Use SVG or PDF as the paper master. PNG is a review or compatibility output.
Prefer PDF for LaTeX when Draw.io uses HTML labels. SVG may contain raster
fallbacks inside `<switch>` elements for viewers without `foreignObject`
support even though normal SVG rendering and the PDF master remain vector.
Treat the paper-icons validator's color-count warning as a review prompt when
it counts both semantic strokes and their light tints; require zero errors and
confirm the palette still has no more than five semantic hues.

## Quality gate

Require all of the following:

- one claim is legible in three to five seconds;
- primary reading order is unambiguous;
- every arrow has a defined relation and valid target;
- the main contribution has stronger hierarchy than context;
- one coherent icon family is used and each icon is semantically necessary;
- all icons are embedded vector data URIs with a source manifest;
- labels remain at least 7 pt at final width;
- panel labels remain at least 8 pt and no more than three type sizes are used;
- the primary font is a permitted sans-serif; monospace appears only in code;
- final SVG/PDF width is 85 mm or 178 mm and review PNG is at least 300 dpi;
- all manuscript figures bind to the same frozen paper palette with zero drift;
- grayscale preserves topology, status, and emphasis;
- no shape, label, arrowhead, group, or icon is clipped;
- `.drawio`, `.icons.json`, SVG, PDF, and review PNG are delivered;
- the final exported files, not only their source, have been inspected.
