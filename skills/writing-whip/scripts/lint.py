#!/usr/bin/env python3
"""Flag mechanical AI-writing tropes (rules: ../SKILL.md; catalog: references/tropes.md, from tropes.fyi).

Usage: lint.py FILE... | lint.py -   (stdin)
Prints `file:line  trope  "snippet"` per hit and a summary. Skips fenced code and inline code.
Only catches surface patterns; behaviours (premise stacking, fractal summaries, invented labels,
rule of three) still need a read-through. Exit code is always 0.
"""
import re
import sys

WORDS = {
    "magic adverb": r"\b(quietly|deeply|fundamentally|remarkably|arguably)\b",
    "delve family": r"\b(delv(e|es|ed|ing)|certainly|utili[sz](e|es|ed|ing)|leverag(e|es|ed|ing)|robust|streamlin(e|es|ed|ing)|harness(es|ed|ing)?)\b",
    "ornate noun": r"\b(tapestry|landscape|paradigm|synergy|load-bearing)\b",
    "serves-as dodge": r"\b(serves|served|stands|stood) as\b",
    "worth noting": r"\b(it'?s|it is) worth (noting|mentioning|pointing out)\b|\bit bears mentioning\b|^\s*(importantly|interestingly|notably),",
    "compulsive counting": r"\b(two|three|four|five|six|seven) (things|reasons|ways|lessons|takeaways|constraints)\b",
    "appeal to familiarity": r"\b(famously|notoriously|as we all know)\b",
    "superficial -ing": r",\s*(highlighting|underscoring|reflecting|showcasing|contributing to)\b",
    "tie-back": r"\bso,? to answer your question\b|\bto bring it back to\b",
    "break it down": r"\blet'?s (break (this|it) down|dive in|unpack)\b",
    "kicker": r"\bhere'?s the (kicker|thing|catch|twist)\b",
    "imagine a world": r"\bimagine a world\b",
    "think of it as": r"\bthink of (it|this) as\b",
    "actually lives": r"\bwhere [\w\s]{1,30} (actually|really) lives\b",
    "vague attribution": r"\b(experts|observers|critics|analysts) (say|argue|believe|note|suggest)|\bindustry reports\b|\bstudies (show|suggest)\b",
    "signposted conclusion": r"^\s*(in conclusion|in summary|to sum up|to summari[sz]e|ultimately),",
    "despite challenges": r"\bdespite (its|these|the) challenges\b",
    "preamble": r"^\s*(great question|certainly!|absolutely!|let me (explain|walk you through)|here'?s (a|the) (breakdown|summary|overview))",
    "promotional": r"\b(seamless(ly)?|unlock(s|ing)? (the|new|unprecedented)|game[- ]chang(er|ing)|cutting[- ]edge|state[- ]of[- ]the[- ]art solution|elevat(e|es|ing) (your|every))\b",
    "negative parallelism": r"\b(it'?s|this is|that'?s|is) not (just |only |merely |about )?[^.;:\n]{1,50}[,;]\s*(it'?s|but|this is)\b|\bisn'?t (just |only )?[^.\n]{1,50}\.\s+it'?s\b",
    "negation-first": r"\b(does not|doesn'?t|do not|don'?t|is not|isn'?t|are not|aren'?t|never)\b[^.\n]{0,60}\b(because|since|as)\b|^[^.\n]{0,40}\bnever\b",
    "not X not Y just Z": r"\bnot [^.\n]{1,30}\.\s+not [^.\n]{1,30}\.\s+(just|only)\b",
    "false range": r"\bfrom [\w\s-]{2,25} to [\w\s-]{2,25},? (and )?everything in between\b",
}
CHARS = {
    "unicode arrow": r"[→←⇒⇐↔➜➔]",
    "smart quote": r"[“”‘’]",
    "decorative emoji": r"[\u2705\u274c\u2728\U0001F680\U0001F4A1\U0001F525\U0001F449]",
}
LINES = {
    "bold-first bullet": r"^\s*([-*+]|\d+\.)\s+\*\*[^*]+\*\*[:.]?\s",
    "wh-header": r"^#{1,6}\s+(why|what|where|how|when)\b",
}
COMPILED = [(n, re.compile(p, re.I | re.M)) for n, p in {**WORDS, **LINES}.items()]
COMPILED += [(n, re.compile(p)) for n, p in CHARS.items()]
SMALL = {"a", "an", "the", "and", "or", "but", "for", "nor", "of", "on", "in", "to", "at", "by", "vs", "with", "from", "as", "is"}


def title_case(heading: str) -> bool:
    words = re.findall(r"[A-Za-z][\w'-]*", heading)
    if len(words) < 3:
        return False
    major = [w for w in words[1:] if w.lower() not in SMALL]
    return bool(major) and all(w[0].isupper() for w in major) and not all(w.isupper() for w in major)


def lint(name: str, text: str) -> int:
    hits, in_fence, words, dashes = 0, False, 0, 0
    for no, raw in enumerate(text.splitlines(), 1):
        if raw.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = re.sub(r"`[^`]*`", "``", raw)
        words += len(line.split())
        dashes += line.count("\u2014") + len(re.findall(r"\s--\s", line))
        found = [(n, m.group(0)) for n, rx in COMPILED for m in rx.finditer(line)]
        heading = re.match(r"^#{1,6}\s+(.*)", line)
        if heading and title_case(heading.group(1)):
            found.append(("title-case heading", heading.group(1)))
        for trope, snippet in found:
            hits += 1
            print(f'{name}:{no}  {trope}  "{snippet.strip()[:70]}"')
    if words and dashes / words * 150 > 1:
        hits += 1
        print(f"{name}  em-dash density  {dashes} em dashes in {words} words (aim for at most 1 per 150 words)")
    return hits


def read_text(path: str) -> str | None:
    """Return the file's text (or stdin for '-'), or None after printing why it can't be read."""
    try:
        if path == "-":
            return sys.stdin.read()
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError as error:
        print(f"{path}: cannot read ({error.strerror})")
        return None


def main() -> None:
    total = 0
    for path in sys.argv[1:] or ["-"]:
        text = read_text(path)
        if text is not None:
            total += lint("stdin" if path == "-" else path, text)
    print(f"{total} mechanical trope hit(s). Behaviours need a read-through (see SKILL.md).")


if __name__ == "__main__":
    main()
