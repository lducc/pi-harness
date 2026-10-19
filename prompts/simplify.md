---
description: Cut the current change down to the simplest code that still works
argument-hint: "[files or focus]"
---
Load the `simple-code` skill. Review ${1:-the uncommitted changes (`git diff`)} against it and simplify: delete speculative options, wrappers, defensive checks, needless try/except, dead code, and comments that restate the code. Run its ruff lint on changed Python files and fix the findings. Keep behaviour identical and confirm it with one quick run. Report what you removed in a few lines.
