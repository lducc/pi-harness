# Contributing

Contributions should improve editability, scientific communication, or
reproducibility—not merely add visual decoration.

## Figure contributions

Include:

- a one-sentence research claim and five-second takeaway;
- editable source (`.drawio`, structured spec, plotting code, or equivalent);
- SVG or PDF vector master and a PNG review preview;
- data and visual-asset provenance;
- the paper palette or an explanation of the shared palette binding;
- a strict validation record when the Draw.io toolchain applies.

Do not submit generated raster artwork as the only source.

## Icon contributions

Only permissively licensed or original icons are accepted. Add:

- SVG source without embedded raster images or `foreignObject`;
- source project and source URL;
- exact license;
- semantic name, tags, category, color type, and recolorability;
- trademark status for brand marks.

Preserve official brand colors. Do not add a logo merely as decoration.

## Code changes

Run:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/*.py tests/*.py
ruff check scripts tests
```

Keep the core Draw.io builder and validators usable with the Python standard
library. Add optional dependencies only for isolated capabilities.

## Pull requests

Keep changes focused, explain the research-communication problem being solved,
and include before/after artifacts for visual changes. By contributing, you
agree that your original contribution is licensed under this repository's MIT
license and that you have the right to submit bundled assets.
