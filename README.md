# pi-harness

My [pi](https://github.com/earendil-works/pi) agent setup. It holds the rules, agents, extensions, skills and the learning loop. Auth, keys, sessions and per-machine memory stay out of the repo.

## Install

Needs pi with its logins already done, plus git, node/npm, python3 and a logged-in `gh` (the repos are private). Works on Linux and WSL.

```bash
git clone https://github.com/lducc/pi-harness.git /tmp/pi-harness
bash /tmp/pi-harness/install.sh
```

The script backs up the old `~/.pi/agent` to `~/pi-agent-backup-<date>.tgz` and checks this repo out over it. Untracked files such as `auth.json` stay. It then links `~/.agents/skills`, clones `vibe-wise` and `exp` into `~/tools`, installs extension and package deps, re-applies the subagent patch and sources the `pi` shell function.

Update with `git -C ~/.pi/agent pull`.

## Contents

### Rules

- `AGENTS.md`: global rules for output, code style, memory, tools, delegation and experiments
- `settings.json`: default model and the package list
- `extensions/guardrails.json`, `sandbox.json`: secrets unreadable, `exp` ledger read-only, prompts before `rm -rf`, `sudo` and destructive git. Subagents run sandboxed.

### Learning loop

- `extensions/learn-mode.ts`: `/learn` gives hints before answers, asks for your plan or bug guess first, leaves `TODO(you)` at design points and asks for an explain-back before commits. `/reveal` gives the full answer. `/ship` (the default) turns it off.
- `extensions/review.ts`: every missed `quiz` becomes a card in `~/learning/cards.jsonl`. `/review` re-asks due cards from memory at 1, 3, 7, 21 and 60 days.
- `prompts/inbox.md`: `/inbox` walks the candidate rules the agent logged in `memory/inbox.md`. You accept, edit or reject each one.

### Extensions

- `ask-user-question.ts`, `quiz.ts`: question popup and graded quiz, sharing one UI lock
- `md-log.ts`: mirrors the session to markdown for reading in Obsidian
- `handoff.ts`: `/handoff <goal>` starts a new session from a generated summary
- `session-usage.ts`: plan quota and context size in the status bar, and suggests `/handoff` on long sessions
- `exp-status.ts`: `exp` ledger summary in the status bar and `/exp`
- `custom-header.ts`: startup header
- `browser/`: headless Chromium tools for frontend debugging
- `web-fetch/`: page to markdown
- `visual-tools/`: renders Mermaid and SVG to PNG for lessons
- `prompt-snippets/`: small reusable prompt rules

### Agents

| Agent | Job |
|---|---|
| `scout` | find files, map code |
| `researcher` | web and paper research with sources |
| `quick` | small one-file code |
| `worker`, `worker-luna` | implement a fully specified task |
| `reviewer` | check a diff, result or claim |
| `mermaid-maker`, `svg-maker` | one verified diagram |

### Skills

- `skills/`: my own skills: `teach`, `visualize`, `simple-code`, `writing-whip`, `pdf-reader`, `analyze-sessions`, `web-debug`, `youtube-transcript`
- `agents-skills/`: third-party skills, linked to `~/.agents/skills` (drawio, LaTeX, figures, frontend design, PDF and others)

### Patches

- `patches/interactive-subagents-provider-ext.patch`: lets subagents load the claude-bridge provider. `pi update` drops it, and `pi-shell.sh` re-applies it.
- `patches/pi-shell.sh`: `pi` shell function. The main session runs unsandboxed and subagents stay sandboxed.
