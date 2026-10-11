# Visual grammar for scientific figures

Use this reference after the primary claim is known. These patterns were
distilled from an LLM-kernel-agent corpus and generalize to systems and machine
learning papers.

## Composition by figure type

| Figure type | Useful default | What should dominate |
| --- | --- | --- |
| System overview | Wide, roughly 2:1; left-to-right stages | Novel stage and feedback path |
| Worked example | Wide, roughly 2:1; aligned before/after columns | The transformation |
| Dataset/taxonomy | Wide panels or tree plus evidence panel | Category structure and prevalence |
| Quantitative comparison | Roughly 1.6–1.8:1 | Baseline-relative result |
| Scaling | Aligned small multiples | Trend and regime change |
| Ablation | Roughly 1.4:1 | Full-vs-removed delta |
| Roofline/SOL | Roughly 1.4:1 | Headroom to a labeled bound |
| Heatmap | Compact matrix | Ordered pattern, not a rainbow |

Treat these as starting proportions, not constraints. Use the target venue's
column width as the real constraint.

## System and method diagrams

Build the main path from three semantic regions:

```text
input or task → generative/search/training core → execution and verification
```

Use shallow nesting. A stage container establishes hierarchy; cards inside it
represent modules or agents. Artifacts on arrows make data transformations
concrete. Use a dark neutral arrow for primary control flow and a semantic color
for feedback, reward, or error.

Prefer one bounded loop over several long return arrows. If the system has
multiple iterations, show the loop protocol once and put changing state inside
it. Do not create a unique shape or color for every module.

## Quantitative charts

Every evidence chart needs a visual anchor. Common anchors include:

- a `1.0×` performance line;
- a named framework or vendor-library baseline;
- a diagonal for measured-versus-reference comparison;
- a roofline or speed-of-light bound;
- an acceptance threshold;
- a directly labeled best point or headroom arrow.

For small multiples, share axes and color mappings when comparison requires it.
Put hardware, workload, precision, or model on a deliberate row/column
dimension. Use one global legend. Sort categories by the comparison readers
should perform, not alphabetically by default.

Use bars for discrete magnitudes, points for estimates with uncertainty, lines
for ordered progress, scatter for relationships, CDFs for distributional
coverage, and heatmaps for genuinely two-dimensional structure.

## Ablations and dynamics

Ablations should test causal components, not merely list configurations. Keep
the full method visually stable and compare two to five removals or
interventions. Use uncertainty bands or intervals when repetitions exist.
Annotate where degradation begins.

For training and search dynamics, separate metrics with different semantics or
scales into aligned panels. Emphasize the curve supporting the claim; recede
diagnostic curves. Mark collapse, plateau, overflow, policy update, or phase
transition events directly.

## Worked examples

Align source, intermediate representation, and output. Use a stable highlight
for each corresponding variable, tile, or region. Crop code to the relevant
lines, preserve monospace typography, and number the operations. Regular grids
communicate tensor layouts better than freehand shapes.

## Color, type, and line system

Start from grayscale. Add three to five semantic colors plus neutral grays.
High saturation should occupy a small fraction of the page and mark important
states or evidence. Avoid gradients, decorative shadows, and colored boxes that
carry no meaning.

Use the paper's body font when practical and a matching monospace face for code.
At final size use approximately 7–9 pt text and 0.8–1.4 pt strokes. Make primary
paths or data 30–50% heavier than supporting structure. Keep backgrounds white
and grid lines quiet.

## Failure patterns to reject

- Figure 1 becomes a miniature of the entire paper.
- Fonts are readable only when zoomed beyond publication size.
- Crossing arrows obscure reading order.
- Icons mix incompatible visual styles.
- Every component has a different color.
- Default plot styling leaves crowded legends and labels.
- Screenshots or low-resolution exports rasterize text.
- Color alone carries the distinction.
- Multiple claims compete without a clear visual hierarchy.
