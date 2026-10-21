---
description: Review candidate harness rules in memory/inbox.md
---
Read `~/.pi/agent/memory/inbox.md`. For each candidate, show the rule and its evidence line, then ask with `ask_user_question`: accept, edit, or reject. Accepted rules: add one line to the right file (`AGENTS.md` for behavior, a skill for a procedure), and in `AGENTS.md` merge it into or replace an existing line so the file does not grow. Add a dated line to `memory/decisions.md`. Rejected rules: move them to `memory/rejected.md` with the date. Then remove every handled candidate from `inbox.md`. Never rewrite a file wholesale.
