# Paper-level color system

Use one palette contract for the entire manuscript. A collection of attractive
figures is not a visual system if the same method, baseline, state, or data type
changes color between figures.

The reusable template is `assets/paper-palette.yaml`. Copy it into the paper
project, set a stable `paper_id` and `palette_id`, assign semantic and chart
roles, then change `status` from `draft` to `frozen` before producing final
figures.

## 1. Separate eligibility from identity

`assets/academic-style.yaml` defines whether a color treatment is academically
acceptable: maximum hues, canonical notation, contrast, white background, and
prohibited effects.

`paper-palette.yaml` defines the paper's identity: exactly which acceptable
colors mean `ours`, baseline, model, data, success, failure, and theory bound
throughout Figure 1–N.

Never copy arbitrary colors from the latest figure into the next one. All
figure tools should consume the same palette file.

## 2. Assign roles once

Freeze these high-value roles first:

| Role | Default treatment |
| --- | --- |
| Ours / focal method | one saturated accent |
| Strong named competitor | one secondary hue |
| Other baselines | neutral gray, varied by line style or marker |
| Upper bound / theory / reference | dark ink or black |
| Verified / positive state | green plus label, check, or solid marker |
| Failure / regression | red plus label, cross, or dashed line |
| Uncertainty | light neutral band derived from stroke gray |
| Canvas / text / grid | one shared neutral system |

Keep `ours` the same color in method diagrams, bar charts, rooflines, ablations,
and training curves. Keep a named baseline the same color when it reappears.
Do not reuse a method color to mean a stage, dataset, or status elsewhere.

Use color for semantic identity, not for enumeration. Five pipeline stages do
not need five unrelated hues. Differentiate repeated stages with position,
labels, boundaries, or tints of a shared semantic hue.

## 3. Derive, do not invent

Use saturated base colors for strokes, focal marks, and direct labels. Derive
card fills, confidence bands, and regions by mixing the same base hue toward
the shared canvas. Do not introduce a new hue merely to obtain a lighter fill.

Use one neutral system for canvas, ink, muted text, grid, borders, and ordinary
baselines. A paper should not alternate between blue-gray, warm gray, and pure
black neutral systems without a measured reason.

Do not let protected brand colors become the general paper palette. A brand
color may identify the actual product or vendor; analytical roles still follow
the paper palette.

## 4. Quantitative-figure policy

For charts:

- highlight `ours`; subordinate ordinary baselines;
- use a secondary hue only for a strong recurring competitor;
- distinguish additional baselines with marker and line style before adding
  more hues;
- keep uncertainty bands lighter than their corresponding series;
- use the same good/bad direction and status mapping across panels;
- never rotate palette order between legends;
- use direct labels when they prevent color-only lookup;
- test grayscale and common color-vision conditions.

Sequential, diverging, and categorical colormaps are data encodings, not method
identity palettes. Declare their variable, domain, midpoint, and direction in
the Figure Contract. Do not reuse a quantitative colormap as a categorical
method palette.

## 5. Existing-paper workflow

When joining an existing manuscript:

1. inspect representative method, quantitative, and failure-analysis figures;
2. inventory recurring entities and their current colors;
3. separate intentional semantic mappings from accidental one-off choices;
4. choose the mapping that preserves the most established reader expectations;
5. record it in `paper-palette.yaml`;
6. repair conflicting figures rather than preserving inconsistency;
7. freeze the palette only after grayscale, contrast, and print checks pass.

If two existing figures use the same color for different meanings, resolve the
collision explicitly. Do not average or silently retain both conventions.

## 6. Draw.io binding and audit

Build each Draw.io figure with the same contract:

```bash
python3 scripts/build_drawio_figure.py figure-spec.json \
  --paper-palette paper-palette.yaml \
  --out figure.drawio \
  --paper-icons-skill /absolute/path/to/paper-icons
```

Validate one source:

```bash
python3 scripts/validate_drawio_figure.py figure.drawio \
  --paper-palette paper-palette.yaml --strict
```

Audit all Draw.io sources together:

```bash
python3 scripts/validate_paper_palette.py \
  --palette paper-palette.yaml figures/*.drawio --strict
```

The builder embeds the palette ID, schema version, and canonical SHA-256 digest.
When a paper palette is bound, per-figure palette overrides must match it
exactly. The validators reject a mismatched ID, changed palette content,
undeclared semantic hue, or a figure that claims a different contract.

## 7. Review gate

Before final export, require:

1. one frozen palette file is stored with the paper;
2. every figure or plotting script consumes that file or an exact generated
   projection;
3. `ours`, recurring baselines, success, failure, and bounds retain their roles;
4. hue is not the only carrier of status or series identity;
5. body text contrast is at least 4.5:1;
6. grayscale and color-vision review preserve the main claim;
7. a cross-figure palette audit reports zero drift.
