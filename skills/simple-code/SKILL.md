---
name: simple-code
description: "The user's code style. Load before writing, editing, or reviewing any code. KISS, YAGNI, Pareto: the smallest plain code that does the job, written as if a careful human typed it by hand and understands every line."
---

# Simple code

The test for every line: would a person who understands this problem have bothered to type it? If not, delete it.

## Write

- Solve the case in front of you. No options, flags, config, plugins, or abstractions for needs nobody stated. Abstract only on the third real repetition.
- Aim for the 20% of code that covers 80% of the value. Name the cases you skipped in one line to the user instead of coding them.
- Plain functions and plain data (dicts, lists, tuples, a dataclass when it earns it). A class only when state and behaviour truly belong together.
- Standard library first. Add a dependency only when it removes a lot of code.
- Imports: only what is used, at the top, no `from __future__ import ...`, no `typing` gymnastics. Type hints on function signatures are fine; skip them where they add noise.
- Let errors raise. No try/except unless there is a real recovery (retry, fallback, a clear user-facing message at the program's edge). Never catch just to log and re-raise, never bare `except`.
- No defensive checks for things that cannot happen, no input validation inside internal code, no `if x is not None` chains for values that are always set.
- Short and flat: early returns, few nesting levels, one obvious loop instead of clever comprehension stacks.
- Names say what things are, so comments are rare. Comment only the why that the code cannot show. No docstring boilerplate, no section-banner comments, no commented-out code.
- Comments must read as if a human typed them in passing: one short line, default to none. A script may open with a one-line usage comment. No multi-line file headers, no experiment results or scores, no project history ("the old run", "commit abc"), no restating what the next line does, no mentions of where the code happens to run (Colab, VM, Slurm).
- Match the surrounding code's idiom, naming, and layout.

## Check

- Lint Python before handing over: `ruff check --config SKILL_DIR/ruff.toml <changed files>`. It flags `__future__` imports, unused code and arguments, commented-out code, re-raise-only try/except, blind excepts, and functions with too many branches or arguments. Fix the code rather than adding `noqa`.
- One small check that the thing works (run it, or one focused test for the core logic). No test suites, fixtures, or mocks unless asked.
- Before handing over, reread the diff and remove: unused code, speculative parameters, wrappers that only call one function, logging nobody reads, and anything you added "just in case".
- When fixing, remove the cause rather than adding a guard around the symptom.
- Report the change in a few lines. Do not explain code the user can read.

## Not this

```python
from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class WordCounter:
    """Counts words in a file."""
    def __init__(self, path: str, lowercase: Optional[bool] = True) -> None:
        self.path = path
        self.lowercase = lowercase

    def count(self) -> dict[str, int]:
        try:
            with open(self.path) as f:
                text = f.read()
        except Exception as e:
            logger.error("failed to read %s: %s", self.path, e)
            raise
        ...
```

## This

```python
from collections import Counter
from pathlib import Path

def word_counts(path):
    return Counter(Path(path).read_text().lower().split())
```
