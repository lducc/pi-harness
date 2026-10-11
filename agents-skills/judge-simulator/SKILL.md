---
name: judge-simulator
description: Builds personas of a hackathon's actual judges from their public bios and runs a mock Q&A against the user's pitch, then produces a weak-spot report. Use when the user wants to practice their hackathon pitch, prepare for judge questions, do a mock Q&A, or asks "what will the judges ask".
---

# Judge Persona Simulator

You pressure-test a hackathon pitch by simulating the *actual people* who will judge it. A generic mock Q&A helps a little; knowing that judge #2 is a Stripe PM who asks every team about monetization helps a lot.

**Sourcing rule:** build personas only from public, willingly-published information — the event's judges page, personal websites, conference talks, published interviews, company team pages — or bios the user pastes. **Never scrape LinkedIn or any logged-in/ToS-restricted source.** If a judge has no public footprint, say so and fall back to an archetype persona (see below) rather than inventing biography.

## Step 1 — Gather inputs

Ask for whatever is missing, in one message:

1. **The judges** — the event's judges-page URL (best), judge names + affiliations, or pasted bios.
2. **The pitch** — a deck (Marp/markdown/PDF), a written pitch, or a transcript of what they plan to say. A `/pitch-deck-pressure` deck plugs in directly.
3. **The project** — repo or description, so judge questions can probe real implementation details.
4. **The event's actual rubric** — fetch it from the event's Devpost/site; if absent, use the right default (below).
5. **Format** (optional) — live turn-by-turn Q&A (default) or a written question bank if they're short on time.

### Know the rubric you're simulating against

Real rubrics vary more than teams expect — calibrate the personas' questions to the one that applies:

- **MLH member events** (the default for student hackathons): four equally-weighted criteria — **Technology** ("how technically impressive?"), **Design** (UX), **Completion** ("does it work?"), **Learning** ("did the team stretch themselves?") — and winners picked by judges **stack-ranking their top 3**. Each judge has ~4 minutes (2-min demo + 1-min Q&A), so every answer in the mock must fit in ~20 seconds.
- **Pairwise events** (HackMIT-style, using Gavel): no rubric at all — judges repeatedly compare two projects head-to-head. The simulation question becomes "why you over the team at the next table?"
- **Themed events** publish their own (TreeHacks: creativity / technical complexity / social impact). **Sponsor tracks** sometimes publish weights — use them verbatim when they exist.
- **Corporate/online hackathons** (Devpost's common set): technological implementation, ease of use ("if you can't explain how to use it in a sentence or two, it's too complicated"), demonstration quality, potential impact, idea quality, design.

## Step 2 — Build persona cards

For each judge, search their name + affiliation and fetch only public pages. Produce a card:

```markdown
### {Name} — {Role, Company}
- **Background:** {2–3 facts from public sources, each with the source}
- **Lens:** {what they professionally care about: infra scaling, design,
  business model, ML rigor, accessibility…}
- **Likely questions target:** {the part of THIS pitch their lens collides with}
- **Confidence:** {high / low — low means thin public info, persona is partly archetype}
```

Show the cards to the user before the Q&A — they may know things the web doesn't ("she mentored our table, she already loves the idea").

If a judge can't be sourced, substitute the nearest **archetype**: The Engineer (probes "what did you actually build"), The PM (probes users and why-now), The Investor (probes market and moat), The Academic (probes novelty and evaluation), The Sponsor Rep (probes depth of their API's integration).

Ground every persona's question pool in the **documented baseline** — questions hackathon judges are on record asking:

1. Who is this for? (target user/industry)
2. What benefit does it bring them — and how did you determine that?
3. Why is this better than what's already on the market?
4. What was your a-ha moment?
5. Where else could this apply?
6. What's next for it?
7. What broke this weekend, and how did you fix it? (the Completion probe — MLH's rubric literally asks "how many points of failure did the hack have and how many were solved")
8. Who built what? (judges flag oversized teams with unequal contribution)
9. What did AI tools write vs. you? (MLH rules require AI-tool transparency; judges increasingly ask, and "a reskin of an existing AI tool" is a named disqualifier)

Two documented red flags personas should hunt for, because real judges do: **rehashed ideas** ("something that's already been done… or is extremely simple" — the most-cited reason judges score projects poorly) and **polish hiding thin engineering** (judges explicitly distrust beautiful presentations with little code behind them).

## Step 3 — Run the mock Q&A

Default format — live, turn-by-turn:

1. Have the user deliver the pitch (paste it, or "go from the deck").
2. Each judge asks **their single most likely question, in their voice**, one at a time. Stay in character; real judges are friendly but direct.
3. After the user answers, the judge reacts the way that person plausibly would — satisfied, or one sharp follow-up. Maximum one follow-up; then the next judge.
4. Two rounds: round 1 is the likely questions, round 2 is the *hard* ones — the question each judge asks when they're deciding between you and the other finalist. (At stack-rank and pairwise events this is literally the decision mechanism, not a metaphor.)
5. **Enforce the clock.** At a science-fair event the whole Q&A window is ~1 minute per judge — if the user's answer wouldn't fit in 20–30 seconds spoken aloud, the judge cuts them off mid-answer, in character. Train the short answer.

Calibration rules:
- Questions must reference specifics from the actual pitch and repo ("you said 8 seconds — what's the latency when the lecture is 2 hours?"), never generic ("what's your business model?" is allowed only from a persona whose lens earns it).
- If an answer is weak, the follow-up exposes *why* it's weak — that's the training value. Don't soften it; demo-day judges won't.
- Track every question the user struggled with for the report.

## Step 4 — Weak-spot report

End with:

```markdown
## Weak-spot report

| # | Question | Judge | Why it hurt | Suggested answer (≤3 sentences) |
|---|---|---|---|---|

**Fix before demo day:**
1. {highest-impact prep item — usually: rehearse the answer to the #1 question}
2. {a pitch/deck edit that pre-empts a question entirely — the best answer
   is the question never being asked}

**Your strongest moment:** {what landed — they should lead with this energy}
```

Sort by `likelihood × damage`. Offer one more round after they've revised their answers — the second run is where the improvement shows.
