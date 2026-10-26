---
description: Review candidate memory and rules in memory/inbox.md
---
Read `~/.pi/agent/memory/inbox.md`. For each candidate, show it with its evidence line and ask with `ask_user_question`: accept, edit, or reject. Put each accepted item in one place, as one dated line:
- a hard rule the agent must always follow: `AGENTS.md`, merged into or replacing an existing line so the file does not grow;
- a procedure: the matching skill;
- a fact about the user, their taste, or research knowledge: the matching note in `memory/` (`me.md`, `taste/`, `research/`), or a new note with a `description:` frontmatter line if none fits.
Move rejected items to `memory/rejected.md` with the date. Remove every handled item from `inbox.md`. Never rewrite a file wholesale.
