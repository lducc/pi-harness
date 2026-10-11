# Evidence, corpus analysis, and figure auditing

## Separate facts from inference

Record three levels of evidence:

1. **Direct evidence**: SVG metadata, PNG software tags, source files, captions,
   or author-provided repositories.
2. **Structural observation**: aspect ratio, panel count, white-space fraction,
   saturation, repeated shapes, alignment, or chart type.
3. **Visual inference**: a likely tool or authoring method based only on
   appearance.

Never report a visual inference as a tool fact. Missing metadata does not mean a
figure was manually drawn.

## Corpus procedure

1. Deduplicate paper identifiers and snapshot the source list.
2. Collect official arXiv HTML first.
3. Preserve HTML, captions, subfigure order, URLs, local paths, and hashes.
4. Retry HTML failures with ar5iv.
5. For remaining papers, preserve official PDF and source archives.
6. Extract or render source-linked figures and page previews.
7. Verify that every paper has one documented provider.
8. Produce contact sheets grouped by a lightweight caption taxonomy.
9. Review samples visually; do not rely on automated classification alone.
10. Publish counts, fallback coverage, errors, and caveats with the conclusions.

Do not equate asset count with figure count. A figure may contain many
subfigure assets, and HTML-only figures may contain no independent image.

## Useful measurements

- paper coverage by provider;
- figure count and assets per figure;
- format distribution;
- median aspect ratio by figure type;
- white, grayscale, dark, and saturated pixel fractions;
- direct tool metadata;
- panel distribution;
- final-size text and stroke dimensions.

Use measurements to reveal patterns, then confirm them on contact sheets. Pixel
statistics do not establish whether a figure communicates well.

## Audit rubric

Score each item as pass, revise, or unknown:

- The claim is singular and defensible.
- The reading order is visible without narration.
- The decisive evidence has a labeled anchor.
- Encodings are consistent and explained.
- Comparisons use honest axes and compatible scales.
- Uncertainty and sample definitions are present where needed.
- Text and strokes work at the venue's final width.
- Grayscale and color-vision checks preserve meaning.
- Source data and visual elements have provenance.
- Editable source and vector output exist.
- The caption defines conditions, metric, baseline, and conclusion.

Lead a redesign report with the highest-impact communication failure. Attach
specific corrections to objects, panels, or encodings rather than offering only
general aesthetic advice.
