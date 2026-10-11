# Tool recipes

Load only the section for the chosen implementation family.

## Matplotlib and Seaborn

Use for data-bound figures. Keep the data preparation separate from rendering
and save the plotted data beside the source.

Recommended defaults:

```python
import matplotlib as mpl

MM = 1 / 25.4
mpl.rcParams.update({
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 8,
    "legend.fontsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "axes.linewidth": 0.8,
    "lines.linewidth": 1.2,
    "savefig.bbox": "tight",
    "savefig.transparent": False,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
})

fig, ax = plt.subplots(figsize=(85 * MM, 58 * MM))
fig.savefig("figure.svg")
fig.savefig("figure.pdf")
fig.savefig("figure.png", dpi=300)
```

Prefer explicit figure sizes in millimeters. Use constrained or manual layout,
then inspect for unintended resizing. Set categorical order and axis limits
explicitly. Keep uncertainty visible. Build accessible palettes with both color
and marker or line-style redundancy when necessary.

For roofline plots, label the bound, knee, hardware, units, and whether points
are measured or predicted. For speedups, show the `1×` line. For log axes, make
the base and tick interpretation clear.

## Graphviz and Mermaid

Use for diagrams whose topology matters more than manual placement. Keep the
graph shallow, direct edges consistently, and cluster only real conceptual
stages. Export SVG and inspect the generated reading order and label sizes.

If exact placement, mixed code snippets, or custom panel composition becomes
central, move to editable SVG or a visual layout tool.

## Editable SVG, Draw.io, Figma, or presentation software

Use a fixed grid and reusable component styles. Define stage container, module
card, artifact, primary arrow, feedback arrow, success, and failure styles
before drawing. Align and distribute objects numerically.

Keep text as text and icons as vectors. Export SVG or PDF without outlining text
unless the publication workflow requires it. Open the export independently to
catch missing fonts, clipped masks, and broken markers.

## TikZ and PGF

Use when exact equation alignment, LaTeX typography, or source-controlled
diagram generation outweighs iteration speed. Centralize colors and node styles.
Compile a minimal standalone figure during iteration. Avoid deeply nested
positioning expressions that make revisions brittle.

## Repeated panels

Generate each panel from one script and one data schema. Use shared axis
construction, category order, palette, and typography. Compose in code when
possible so a data update cannot silently desynchronize panels.

## Export and inspection

Always keep the editable source. Prefer SVG/PDF masters and treat PNG as a
preview or raster-only venue output. Inspect:

- the vector file in an independent viewer;
- the final-size raster preview;
- grayscale output;
- text selection or embedded-font behavior;
- bounds, clipping, alpha, and line joins.
