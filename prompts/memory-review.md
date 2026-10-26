---
description: Monthly check of the memory for stale, wrong or bloated notes
---
Read every note in `~/.pi/agent/memory/`. Report, without editing anything:
1. Lines dated more than 60 days ago, or undated, that may be stale. Check each against the current files where you can.
2. Contradictions between notes, or between a note and `AGENTS.md`.
3. `me.md` over 60 lines, and notes that should be split or merged.
4. From sessions of the last 30 days (`analyze-sessions` skill, search the user's messages), corrections and stated preferences that are not in memory yet. Add these to `memory/inbox.md` as candidates with one line of evidence each, in the user's words.
Then ask with `ask_user_question` which of points 1-3 to fix, and fix only those.
