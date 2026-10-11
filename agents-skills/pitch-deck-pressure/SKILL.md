---
name: pitch-deck-pressure
description: Generates a timed hackathon pitch (Marp slide deck and/or table-demo script) from a GitHub repo plus a short description, with 1-minute, 2-minute, 3-minute, or 5-minute versions and per-slide speaker notes. Use when the user asks for a pitch deck, demo-day slides, a hackathon presentation, a judging table script, or help pitching their project under a time limit.
---

# Pitch Deck Under Pressure

You turn a repo + a two-sentence description into a pitch a sleep-deprived team can deliver cold. The arc that wins: **problem → insight → demo → traction → ask**. Everything is sized to the time limit, because the #1 way teams lose is getting cut off before the demo.

**Know the format first.** Most student hackathons — including everything MLH runs — use **science-fair judging**: judges rotate to your table with ~4 minutes each (MLH's official budget: 2 min demo + 1 min Q&A + 1 min walking), see your project in 3 rounds by 3 different judges, and MLH's rules say outright that "pitches and presentations are discouraged" in favor of demos. For that format the deliverable is a **2-minute table script**, not slides. Slides are for finals rounds, sponsor stages, and corporate hackathons. This skill produces either — ask which one they're facing.

## Step 1 — Gather inputs

Ask for whatever is missing, in one message:

1. **Repo** — local path or GitHub URL.
2. **Description** — ~2 sentences. If they ramble, you'll distill it.
3. **Format & time limit** — science-fair table (default 2 min) or stage pitch (1 / 3 / 5 min). If they don't know: check the event's site; MLH member events are science-fair.
4. **Audience** (optional) — general judges vs. a sponsor track changes what "traction" means.

## Step 2 — Mine the repo

Read, in priority order: `README`, the main entry point, the most-edited source files (`git log --stat` if local), and any demo/screenshot assets. Extract:

- **What it actually does** — verified from code, not the README's aspirations. If the README promises X and the code only does Y, the deck claims Y. A judge probing a false claim is fatal.
- **The insight** — the one non-obvious technical or product decision. This is usually in the architecture: an unusual data flow, a clever model choice, a constraint they turned into a feature.
- **Traction evidence** — commit count and span ("41 commits in 30 hours"), working features, tests passing, deployed URL, anything quantifiable.
- **The demo path** — the exact sequence of user actions that shows the core loop working.

## Step 3a — Science-fair format: the table script

For table judging, output a **2-minute script** structured on AngelHack's "Golden Points" template (their published demo guidance): **30 seconds problem/solution → 60 seconds live demo → 30 seconds next steps**. Format it as cue lines with timestamps, plus:

- **The handoff line** — judges remember projects they *touched*. Script the moment you turn the laptop around: "want to try it?"
- **The rubric check** — MLH judges score four equally-weighted criteria: **Technology, Design, Completion, Learning**. The script must hand each judge evidence for all four in their 2 minutes — the Learning line ("we'd never touched WebRTC before this weekend") is the one teams always forget, and it's 25% of the score.
- **Three pitch lengths** — also output the one-breath version (~10 words) and the 30-second version; teams pitch in hallways, demo expos, and elevator rides all weekend, and judges talk to each other.
- Don't memorize the script — tell the team to memorize the *turns* (the transitions); it survives interruptions, and judges interrupt.

## Step 3b — Stage format: the deck

For stage pitches, output a single Marp markdown file (template: [templates/deck.md](templates/deck.md)). Slide budget by time limit:

| Time | Slides | Arc |
|---|---|---|
| **1 min** | 3 | problem+insight (merged) → demo → ask |
| **3 min** | 6 | title → problem → insight → demo (2 slides) → traction+ask |
| **5 min** | 8–9 | title → problem → who-has-it → insight → how-it-works → demo (2) → traction → ask |

Hard rules:

- **≤ 20 words per slide.** Slides are billboards; the talking happens in speaker notes. If a slide needs a paragraph, it's two slides or it's notes.
- **The demo slide is a cue card, not a screenshot.** It says what the audience is about to see ("Watch: lecture in → flashcards out, 8 seconds") so the demo lands even if wifi doesn't.
- **One number per traction claim.** "41 commits, 6 features, deployed" beats adjectives.
- **The ask is concrete.** "Try it at <url>", "We want the <sponsor> prize because <criterion>", or "We're continuing this — talk to us." Never end on a thank-you slide; end on the ask.
- **Speaker notes carry timings.** Each slide's notes start with `<!-- 0:00–0:25 -->` style cumulative timestamps so the presenter knows if they're behind *while presenting*. Total must come in 10% under the limit — judges cut you off, they never give time back.

## Step 4 — Pressure-test and hand off

After writing the deck:

1. **Read the notes aloud-speed check:** ~150 words/minute. Count the words in the speaker notes; if over budget, cut from the problem slides, never the demo.
2. Tell the user how to render it: `npx @marp-team/marp-cli@latest deck.md -o deck.pdf` (or `.pptx`/`.html`; `--notes` exports the speaker notes to a text file for rehearsal). PDF/PPTX export needs Chrome, Edge, or Firefox installed; HTML doesn't.
3. Offer the other time versions — teams often discover at check-in that "3 minutes" meant "2 minutes including setup". Generating the 1-min fallback now costs nothing.
4. Demo insurance: tell the team to skip mundane flows in the live demo (no signups — be pre-logged-in, demo text pre-copied to the clipboard) and to keep a screen recording of the working demo on a phone as backup.
5. Offer to hand the pitch to `/judge-simulator` for a mock Q&A if that skill is installed.
