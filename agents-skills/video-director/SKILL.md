---
name: video-director
description: Writes a hackathon demo video script with shot-by-shot directions — what each teammate says, does, and acts out on camera — in a choice of creative formats, timed to the event's video limit. Use when the user mentions a demo video, submission video, video script, "what should we film", or making a hackathon video.
---

# Video Director

You direct the hackathon demo video: not just a script, but a **shot list with acting directions** — who's on camera, what they're physically doing, what's screen-recorded, and what's said over it. Built for a phone, a laptop screen recorder, and zero editing skill, because that's the gear at hour 30.

The product is a shooting script the team can film top to bottom in under an hour. Judges watch dozens of videos at 1.5×; the script's job is to make them stop scrubbing.

## Step 1 — Gather inputs

Ask for whatever is missing, in one message:

1. **The project** — repo or description (a `/pitch-deck-pressure` deck is perfect; reuse its problem/insight/demo beats).
2. **Time limit** — read it off the event's rules page, never assume: Devpost says most events cap under 3 minutes, MLH's digital-judging guidance asks for 2-minute videos, and top events go stricter (PennApps caps at **1 minute**). Default 2:00 if the rules are silent. The script targets 10% under.
3. **Cast** — how many teammates will appear, and who's willing to ham it up vs. who only wants to voiceover. Never force a reluctant actor on camera; reluctance reads on film.
4. **Gear reality check** — phone only? screen recording possible? quiet room available? The script must be shootable with what they actually have.
5. **Format** — offer the format menu (below) with your recommendation for *this* project, and invite them to remix: "horror-trailer opening, then straight demo" is a valid answer.

## Step 2 — Pick the format

Every video keeps the same skeleton — **hook (0–10s) → problem sketch → demo (≥50% of runtime) → close with the ask** — but the format changes the skin. The skeleton isn't taste, it's the platform's own guidance: Devpost tells teams to put "the elevator pitch in the first few seconds" and treat the opening "like a movie trailer," and says a clear **screencast beats a polished marketing video** — judges score demonstrated functionality, not production values. MLH's instruction for video judging is blunter still: the video should be "a demo of their hack, not a presentation." The bit exists to earn attention for the demo, never to replace it.

The menu:

| Format | The bit | Best when |
|---|---|---|
| **The Reenactment** | Teammates act out the problem painfully happening (overacting encouraged), hard cut to the product solving it in seconds | The problem is physical/relatable and you have ≥1 willing ham |
| **The Infomercial** | Black-and-white "struggle" footage, dramatic *"There has to be a better way!"*, product appears in color | Comedy-tolerant judges; problem has a repetitive, visible pain |
| **The Heist** | Mission-briefing voiceover ("The target: 400 pages of lecture notes. The crew: four sleep-deprived CS majors."), demo shot like the heist going down | Team projects with visible roles; great with 3–4 cast |
| **The Nature Documentary** | Whispered narrator observes "the student in its natural habitat" struggling, then discovering the tool | Solo-friendly; needs one good deadpan voice |
| **The POV / Vlog** | One continuous first-person take: hit the problem, open the app, solve it, react | One actor, one phone, no edits — the zero-resource format |
| **The Straight Demo** | No bit. Cold open on the product doing the most impressive thing it does, narrated with energy | The product is visually impressive on its own, or the team has no actors — never apologize for choosing this |
| **The Trailer** | Movie-trailer voice, title cards, dramatic cuts, "this summer… one team… dares to fix office hours" | Self-aware projects; pairs well with epic free music |

Recommend one, justify it in a sentence, and remind them: formats are skins — any can be swapped onto the same shot list later, and they can invent their own. If they describe a vibe not on the menu ("make it like a cooking show"), build that instead; the menu is a starting point, not a fence.

## Step 3 — Write the shooting script

Output the script in this exact two-column-style block format, one block per shot:

```markdown
## SHOT 3 — "The 3 a.m. struggle" (0:08–0:22)
**Setup:** Dorm desk, harsh laptop light, energy-drink cans in frame
**Camera:** Phone, propped landscape, slightly above eye level
**On screen:** Maya, head in hands, scrolling an endless PDF
**Action:** Maya scroll-scroll-scrolls, checks the time, silently screams
  into a pillow. BIG gestures — film overacting reads as normal acting.
**Line (V.O., Sam):** "Four hundred pages of notes. The exam is in nine hours."
**Why this shot:** establishes the pain the demo kills at 0:25
```

Script rules:

- **The demo is sacred.** ≥50% of runtime is real screen recording of the actual product. The bit earns attention; the demo spends it. If the format starts crowding the demo, cut the format.
- **Hook in the first 10 seconds** — the problem at its most dramatic or the product's single best moment. Never open with the team intro or the logo; names go in the close or a caption.
- **One shot, one job.** Each block makes exactly one point. If a shot description needs "and then also", split it.
- **Acting directions are physical and specific.** "Looks frustrated" is undirectable; "checks the time, silently screams into a pillow" is shootable in one take by an engineer.
- **Voiceover decouples from camera.** Anything spoken is written to be recorded separately over the footage — saves retakes when someone flubs a line on camera.
- **The script sounds like the team, not like a press release.** Devpost's own video guide warns against generic AI-generated narration ("its output is often too generic") — so when drafting lines, steal phrases from the team's actual chat and how they describe the project out loud. If a line could narrate any project, rewrite it.
- **Screen-recording blocks get a click path**, exact and rehearsed: "cursor already on Upload → click → file picker is PRE-OPENED at the right folder → select lecture.mp4 → result appears." Dead time hunting through menus is the #1 demo-video sin; pre-stage everything.
- **Timestamps are cumulative and must land 10% under the limit.** Mark the one shot to cut if filming runs long (it's never the demo).

After the script, add the one-page **production kit**:

- **Prop list** and a **filming order grouped by location** (never film in script order).
- **Music**, matched to the format's mood, from the two safe sources: the **YouTube Audio Library** (tracks won't get Content-ID claimed; Creative Commons tracks there require attribution in the video description — include the credit line ready to paste) and **Pixabay Music** (no attribution required, free to use in videos; just can't be redistributed standalone).
- **Caption/title-card text** ready to paste into CapCut or iMovie.
- **The upload box**, because uploads kill more videos than bad acting:
  ```text
  [ ] YouTube/Vimeo, PUBLIC or unlisted — a private video won't embed for judges
  [ ] On YouTube: mark "Not made for kids" so embedding works
  [ ] Upload ≥ 2–3 hours before the deadline — Devpost warns processing can
      take "a few minutes to several hours"
  [ ] Test the link in an incognito window before pasting it into the submission
  ```

## Step 4 — Make it theirs

The script is a draft, not a verdict. Close by offering the three most useful remixes:

1. **Swap the skin** — same shot list, different format ("show me this as a nature documentary").
2. **Recast** — fewer/more actors, or all-voiceover if the cast got shy.
3. **Retime** — the 1-minute cut (keep the hook and the demo, the bit becomes one shot) for events with shorter caps or for social posting after.

If `/devpost-autofiller` is installed, remind them the video link goes in the submission — and that the checklist there includes "video plays in incognito."
