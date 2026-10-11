# paper-icons

An academic figure-authoring skill with semantic icon search, structured
JSON-to-SVG composition, vector PDF/PNG export, and deterministic quality checks.
The catalog currently indexes 581 vector icons, including 32 on-demand Lucide
assets.

Agent instructions and the complete workflow live in `SKILL.md`.

## Core commands

```bash
SKILL=$HOME/.claude/skills/paper-icons

python3 "$SKILL/scripts/search_icons.py" "retrieval database" --limit 8
python3 "$SKILL/scripts/compose_figure.py" spec.json \
  --out figure.svg --pdf figure.pdf --png figure.png
python3 "$SKILL/scripts/validate_figure.py" figure.svg --strict
python3 "$SKILL/scripts/recolor.py" lucide-brain --color 2563EB
```

The core search, SVG composition, and validation paths use only Python's standard
library. PDF/PNG rendering and contact sheets require `rsvg-convert` from librsvg.
Pillow and NumPy are needed only for the rare case of recoloring a PNG that has no
SVG source.

Brand logos are trademarks of their owners. Use them only for academic
identification/comparison and preserve official colors.
