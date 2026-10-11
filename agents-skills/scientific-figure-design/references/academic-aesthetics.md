# Academic figure aesthetics

Use this file as a hard publication constraint, not as optional decoration.
Apply it to system diagrams, model architectures, worked examples, quantitative
charts, and icon-assisted Draw.io figures unless the target venue specifies a
stricter rule.

The machine-readable counterpart is `assets/academic-style.yaml`. The Draw.io
builder and validator consume that file; keep both files semantically aligned.
For a multi-figure manuscript, also use one copy of
`assets/paper-palette.yaml` as the frozen cross-figure color contract and read
`references/paper-color-system.md`.

## 1. Governing principle

Optimize for accurate comparison, rapid comprehension, and reproducibility at
the final printed size. A scientific figure is not a poster, dashboard, product
mockup, or icon collage.

Require:

- one primary claim;
- one unambiguous reading order;
- a visible evidence anchor or mechanism;
- stable semantic encodings;
- editable source and provenance;
- readability without zooming.

Reject visual polish that weakens comparison or invents unsupported meaning.

## 2. Publication geometry

Design at the actual manuscript width:

| Format | Target width |
| --- | ---: |
| Single column | 85 mm; acceptable venue range 82–90 mm |
| Double column | 178 mm; acceptable venue range 170–180 mm |

Use a wide canvas for system overviews and worked examples, normally around
1.8–2.2:1. Use a more compact 1.3–1.7:1 canvas for ablations, rooflines, and
most quantitative charts.

Keep:

- at least one label-height between text and unrelated marks;
- at least one arrowhead-length between a bend and its target;
- consistent panel gaps;
- aligned baselines and equal dimensions for repeated modules;
- enough outer margin that no arrowhead, badge, or panel label is clipped.

For generated Draw.io artifacts, retain the full-page `canvas-bounds` cell and
export final masters with zero external border. Put all required whitespace
inside the academic canvas. This keeps source-space point-size calculations
consistent with the final SVG/PDF width.

Do not fill all available whitespace. Whitespace establishes grouping and
hierarchy.

## 3. Typography

Use one sans-serif family for diagrams and charts unless the manuscript
requires a matching serif family. Default:

```text
Arial, Helvetica, sans-serif
```

Use one monospace family only for code:

```text
SFMono-Regular, Menlo, Consolas, monospace
```

Hard limits at final printed size:

| Element | Preferred | Absolute minimum |
| --- | ---: | ---: |
| Main node or axis label | 8–9 pt | 7 pt |
| Secondary label or edge label | 7–8 pt | 7 pt |
| Panel label | 9–10 pt bold | 8 pt |
| Code | 7.5–8.5 pt | 7 pt |

Use no more than three visible type sizes in one figure. Use regular weight for
secondary content, semibold or bold for focal labels, and avoid light weights
that disappear in print.

Write short parallel phrases:

```text
Collect → Filter → Optimize → Evaluate
```

Avoid mixed grammar:

```text
Data collection → Filtering stage → We optimize → Evaluation results
```

Do not:

- use all caps for ordinary node labels;
- put paragraphs inside nodes;
- shrink text to rescue an overcrowded layout;
- mix more than two font families;
- rasterize labels in the master artifact;
- use underlining as decoration.

Do not apply the monospace family to ordinary labels merely because the subject
is software. Declare code-bearing nodes explicitly; all other visible text uses
the primary sans-serif.

## 4. Lines, arrows, and borders

At final size:

| Mark | Width |
| --- | ---: |
| Supporting border or grid | 0.8–1.0 pt |
| Primary data/path line | 1.0–1.4 pt |
| Emphasized result or contribution | up to 1.6 pt when necessary |

Use a stable arrow grammar:

- solid: primary data or execution flow;
- dashed: feedback, optional control, failure, or supervisory signal;
- thin neutral: dependency or grouping;
- double headed: symmetric exchange only.

Every non-obvious edge needs a short relation label. Keep labels off arrowheads
and node interiors. Route feedback through a dedicated corridor. Avoid crossings;
when unavoidable, reroute or split the panel.

Use rounded corners for modules, not for data bars or axes. Use group containers
only for real ownership, phase, device, or trust boundaries.

## 5. Color

Start with a grayscale skeleton. Add color only after hierarchy and topology
work without it.

For a paper with multiple figures, create the paper-level palette before final
rendering. Give it a stable `paper_id` and `palette_id`, freeze it, and bind
every editable source or plotting script to that same file. The academic style
determines whether colors are permissible; the paper palette determines which
permissible color owns each recurring semantic role.

Use:

- one neutral ink and gray scale;
- at most five semantic hues;
- light tints for regions and cards;
- saturated color for focal strokes, status, or data.

Encode editable-source colors canonically as six-digit `#RRGGBB`. Do not use
named colors, `rgb(...)`, or short hex because they weaken deterministic audit
and provenance.

Default semantics:

| Meaning | Color |
| --- | --- |
| Data, infrastructure, normal path | Blue `#2563EB` |
| Model, agent, generation | Purple `#7C3AED` |
| Optimization, execution, caution | Orange `#B45309` |
| Verified success | Green `#15803D` |
| Failure, rejection, regression | Red `#B91C1C` |
| Context and baseline | Neutral `#64748B` |

Do not rely on red versus green alone. Pair status color with a label, icon,
shape, line style, or position. Preserve the same semantic mapping throughout
the paper.

Keep the focal method, named competitors, ordinary baselines, theory bounds,
success, and failure visually stable across Figure 1–N. Use the same base hue
for a recurring entity in system diagrams and quantitative charts. Derive
lighter cards and uncertainty regions from that base hue instead of inventing a
new color. Do not rotate legend colors between figures.

Maintain at least `4.5:1` contrast for visible text against its effective card,
label, or canvas background. Do not hide text by matching its fill or by using a
low-contrast pastel.

Reject:

- rainbow stage coloring;
- decorative gradients;
- glow, glass, bevel, or drop shadows;
- dark or textured backgrounds for ordinary paper figures;
- low-contrast pastel text;
- brand colors used as the general palette.

## 6. Icons

Treat icons as semantic anchors. Use at most one icon per node and normally one
general icon family per figure. Keep icons around 20–32% of node height.

Prefer outline Lucide or Tabler icons for technical figures. Use a brand mark
only to identify the actual named product, framework, model, or vendor. Preserve
protected brand colors and record the source.

An icon must:

- remain understandable with its label;
- match the visual weight of neighboring icons;
- be vector in the editable source;
- be embedded for portable Draw.io delivery;
- appear in the source manifest.

Keep icon geometry approximately square, make the icon a child of its semantic
node, and reject nested raster `<image>` or HTML `foreignObject` content inside
an SVG wrapper.

Omit an icon when it adds no information. Never replace a metric, code sample,
equation, or tensor layout with a pictogram.

## 7. Quantitative charts

Make comparison truthful before making it attractive:

- label units and experimental conditions;
- show uncertainty when repeated measurements exist;
- use a visible baseline, `1×` line, theory bound, diagonal, or threshold;
- share scales across panels when readers must compare them;
- order categories by the analytical question;
- use direct labels when they reduce legend lookup;
- keep grid lines thin and subordinate.

Do not use:

- 3D bars or pies;
- truncated axes that exaggerate effects without unmistakable disclosure;
- smoothing that hides variability;
- dual axes without a compelling, explicitly labeled reason;
- icons in place of quantitative marks;
- more precision in labels than the experiment supports.

## 8. System and method diagrams

Keep the primary scan to three to five major stages. Give the novel component
stronger hierarchy than context and baselines. Show concrete artifacts—data,
code, profile, result—at the point where they change.

Place one feedback loop in a bounded corridor. Use nested groups only when they
answer who owns, executes, or constrains the child nodes. Do not recreate the
entire paper inside Figure 1.

## 9. Effects and prohibited styling

The default academic style prohibits:

- gradients;
- shadows;
- glass effects;
- faux 3D or isometric shapes;
- comic or hand-drawn modes;
- emoji;
- raster image cells;
- dark canvas backgrounds;
- stock-photo backgrounds;
- decorative illustrations unrelated to the claim;
- animated connectors in the submitted artifact.

Allow an exception only when it encodes a real variable. Document the proposed
exception in the Figure Contract, then obtain an explicit human-reviewed
waiver. The automatic strict gate does not read exceptions and must continue to
report the underlying violation; documentation alone never grants a silent
pass.

## 10. Export and validation

Deliver:

- editable source;
- SVG or PDF vector master;
- PNG review image at 300 dpi or greater;
- icon/source manifest when icons are used;
- completed Figure Contract;
- caption and validation record.

The final exporter must use border `0`, verify that the SVG viewBox matches the
academic canvas, normalize the PDF page to the declared 85 mm or 178 mm width
when Ghostscript is available, and produce the PNG at no less than 300 dpi.

Check:

1. actual final width;
2. minimum 7 pt text;
3. no more than three visible type sizes;
4. one primary font family plus optional monospace;
5. semantic hues no greater than five;
6. stroke widths remain legible;
7. no gradients, shadows, or glass effects;
8. grayscale preserves meaning;
9. color-vision distinctions remain redundant;
10. no clipping, overlap, disconnected nodes, or invalid icon payloads;
11. the five-second and caption tests pass.
12. every figure in a manuscript binds to the same frozen palette ID and
    SHA-256, with zero cross-figure drift.

Treat every strict validation warning as a failed automatic quality gate until
it is fixed. `academic_style.exceptions` is an audit record only: the validator
does not consume it. A venue-specific deviation may proceed only after an
explicit human review records a scoped waiver; it must never pass silently.
