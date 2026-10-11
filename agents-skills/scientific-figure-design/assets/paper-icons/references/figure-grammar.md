# Academic Figure Grammar

## Contents

1. Figure sentence
2. Archetype selection
3. Semantic inventory
4. Layout and hierarchy
5. Arrows and boundaries
6. Typography and final-size geometry
7. Color and accessibility
8. Common failure modes

## 1. Figure sentence

Write one sentence in this form:

> This figure shows that **[mechanism or comparison]** transforms/relates **[inputs]** into **[outcome]** under **[important constraint]**.

Make the dominant visual path express that sentence. Move details that do not support it to the caption, appendix, or a separate panel.

## 2. Archetype selection

| Research message | Use | Avoid |
| --- | --- | --- |
| Ordered transformations | Pipeline | A freeform architecture with arbitrary arrows |
| Components and interfaces | Layered architecture | A row of equal boxes |
| Iterative refinement or control | Feedback loop | A pipeline with a backward arrow added as an afterthought |
| Method A versus B | Mirrored comparison | Two unrelated miniature diagrams |
| Repeated configurations or ablations | Aligned grid | Decorative cards with different geometry |
| Taxonomy or dependency | Tree / hierarchy | A network graph without hierarchy |
| Evidence supporting a claim | Chart + callouts | Icons standing in for quantitative evidence |
| End-to-end paper summary | Graphical abstract | A dense copy of the full method figure |

Use multiple panels only when each panel answers a distinct sub-question. Give panels short labels `(a)`, `(b)`, and use the same visual vocabulary across them.

## 3. Semantic inventory

Classify every item before drawing:

- **Entity:** data, model, agent, user, hardware, benchmark.
- **Transformation:** train, retrieve, compile, optimize, filter, evaluate.
- **State:** candidate, verified, failed, cached, final.
- **Boundary:** system, trust zone, training/inference split, device boundary.
- **Evidence:** metric, observation, result, example.
- **Relation:** data flow, control flow, dependency, comparison, feedback.

Represent different classes differently. For example, use rounded rectangles for entities, verb labels for transformations, and dashed containers for boundaries. Do not use identical cards for every semantic class.

## 4. Layout and hierarchy

- Put the main reading path on the strongest axis: left-to-right for processes, top-to-bottom for hierarchies.
- Give the main contribution more area or stronger contrast than context and baselines.
- Align repeated elements and equalize their dimensions.
- Keep at least one node-width of whitespace between independent branches.
- Use nested containers only for real ownership or execution boundaries.
- Keep edge crossings near zero. If crossings are unavoidable, reroute or split the panel.
- Prefer 3–5 major stages in the main scan. Collapse implementation details into labeled groups.

Use icons at 20–32% of node height. A larger icon becomes an illustration and competes with the label.

## 5. Arrows and boundaries

Define an arrow grammar and keep it stable:

| Style | Recommended meaning |
| --- | --- |
| Solid arrow | Primary data or execution flow |
| Dashed arrow | Optional, supervisory, or control signal |
| Thin gray line | Structural dependency |
| Double-headed arrow | Symmetric exchange only |
| Loop arrow | Iteration with a named stopping or update condition |

Label any edge whose meaning is not obvious. Place labels near the edge, not inside a node. Arrowheads must stop at the target boundary, not run under the target.

Use boundaries sparingly. A dashed container should answer “what owns or executes these nodes?” A tinted region should encode a real phase or domain, not decorate empty space.

## 6. Typography and final-size geometry

Design at the final paper width:

- Single column: 82–90 mm; use 85 mm by default.
- Double column: 170–180 mm; use 178 mm by default.
- Target body labels: 8–9 pt.
- Absolute minimum for secondary text: 7 pt.
- Use no more than three type sizes.
- Use sentence case and short noun/verb phrases.
- Keep labels parallel: `Collect`, `Filter`, `Optimize`, `Evaluate`, not mixed sentence styles.

Print or rasterize at final width during review. A zoomed SVG can hide unreadable typography.

## 7. Color and accessibility

- Start in grayscale; add color only to encode meaning.
- Use one primary accent and at most one secondary accent in ordinary method figures.
- Use light tints for regions and saturated colors for focal strokes or marks.
- Ensure text contrast is at least 4.5:1 for normal text when practical.
- Pair status color with a label or icon; do not rely on red versus green alone.
- Preserve the same color meaning across all paper figures.
- Check grayscale: the hierarchy should survive.

Brand colors are identifiers, not palette colors. Keep logos small and subordinate to the scientific content.

## 8. Common failure modes

- **Icon collage:** many pictograms, little causal structure. Replace with a clear path and fewer icons.
- **Card dashboard:** every concept receives an equal rounded card. Introduce semantic shape and hierarchy.
- **Arrow spaghetti:** edges express afterthoughts. Reorganize topology before styling.
- **Caption inside figure:** paragraphs compensate for weak structure. Move prose to the manuscript.
- **Rainbow stages:** color encodes sequence redundantly. Use position for sequence and color for a meaningful variable.
- **Tiny subfigure:** an entire architecture is squeezed into one panel. Split or abstract.
- **False precision:** decorative gradients, shadows, and 3D effects imply meaning they do not have. Use flat vector geometry.
- **Mixed icon languages:** outline, filled, emoji, and brand art appear together. Keep one family and one visual weight.
