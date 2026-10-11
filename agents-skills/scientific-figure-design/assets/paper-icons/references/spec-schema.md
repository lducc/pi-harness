# Figure Spec Schema

## Contents

1. Minimal spec
2. Top-level fields
3. Nodes
4. Edges
5. Groups and annotations
6. Layouts
7. Export behavior

## 1. Minimal spec

```json
{
  "metadata": {
    "title": "Training and evaluation pipeline",
    "description": "Data is filtered, used for training, and evaluated on a held-out benchmark."
  },
  "figure": {
    "column": "double",
    "layout": "pipeline",
    "direction": "horizontal"
  },
  "nodes": [
    {"id": "data", "label": "Raw data", "icon": "lucide-database"},
    {"id": "train", "label": "Train model", "icon": "lucide-brain", "tone": "accent"},
    {"id": "eval", "label": "Evaluate", "icon": "lucide-target", "tone": "success"}
  ],
  "edges": [
    {"from": "data", "to": "train", "label": "filter"},
    {"from": "train", "to": "eval"}
  ]
}
```

## 2. Top-level fields

- `metadata.title` and `metadata.description`: required for accessible SVG metadata; not drawn as an internal title.
- `figure.column`: `single` or `double`. Defaults to `double`.
- `figure.layout`: `pipeline`, `grid`, or `freeform`.
- `figure.direction`: `horizontal` or `vertical` for pipeline.
- `figure.width`, `figure.height`: optional viewBox dimensions. Keep the physical width controlled by `column`.
- `figure.columns`: number of columns for grid.
- `figure.panel_label`: optional `(a)` label at the upper-left.
- `figure.heading`: optional short heading drawn inside the canvas. Omit for most paper figures.
- `figure.palette`: optional overrides for `accent`, `secondary`, `success`, `warning`, `danger`, `ink`, `muted`, `stroke`, and `canvas`.

## 3. Nodes

Each node requires:

- `id`: unique identifier used by edges.
- `label`: short visible label.

Optional node fields:

- `subtitle`: one short secondary line.
- `icon`: catalog icon ID.
- `tone`: `neutral`, `accent`, `secondary`, `success`, `warning`, or `danger`.
- `shape`: `round`, `rect`, `pill`, `database`, or `circle`.
- `badge`: compact status text in the upper-right.
- `group`: group ID.
- `x`, `y`, `w`, `h`: required for `freeform`; optional overrides elsewhere.

Use verb phrases for transformation nodes and noun phrases for entities. Keep labels under roughly 28 characters when possible.

## 4. Edges

Each edge requires `from` and `to`.

Optional fields:

- `label`: short relation or payload.
- `tone`: palette tone; defaults to `neutral`.
- `style`: `solid` or `dashed`.
- `route`: `orthogonal`, `straight`, or `curve`.
- `arrow`: `end`, `both`, or `none`.

Edges are rendered before nodes. The composer attaches them to node boundaries and provides a light label backing.

## 5. Groups and annotations

Groups:

```json
{"id": "runtime", "label": "GPU runtime", "tone": "accent", "style": "dashed"}
```

Assign nodes with `"group": "runtime"`. Group bounds are derived from node geometry.

Annotations:

```json
{"x": 650, "y": 60, "text": "Our contribution", "tone": "accent"}
```

Annotations are small callout pills. Use them for a contribution marker or constraint, not for paragraph text.

## 6. Layouts

### Pipeline

Places nodes on one axis. Use 3–6 stages. Switch to vertical for a single-column figure with long labels.

### Grid

Places nodes in equal cells. Use for aligned comparisons or repeated ablations. Set `figure.columns`.

### Freeform

Requires explicit node coordinates. Use for layered architectures, branches, or feedback loops. Keep all coordinates inside the selected canvas:

- Double-column default viewBox: `1080 × 480`
- Single-column default viewBox: `560 × 420`

Coordinates refer to each node's upper-left corner.

## 7. Export behavior

```bash
python3 scripts/compose_figure.py spec.json \
  --out figure.svg --pdf figure.pdf --png figure.png --dpi 180
```

- SVG is the editable source.
- PDF is the preferred LaTeX artifact.
- PNG is rendered at the physical paper width and requested DPI for review or slides.
- Missing `rsvg-convert` affects only PDF/PNG export; SVG generation still works.
