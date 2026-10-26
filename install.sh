#!/usr/bin/env bash
# Install this harness into ~/.pi/agent. Leaves auth.json, sessions, memory and env alone.
set -euo pipefail
A="$HOME/.pi/agent"
REPO="${1:-https://github.com/lducc/pi-harness.git}"

mkdir -p "$A" "$HOME/tools" "$HOME/.agents" "$HOME/.local/bin"
cd "$A"
if [ ! -d .git ]; then
  tar czf "$HOME/pi-agent-backup-$(date +%F).tgz" --exclude=sessions --exclude=npm --exclude=install --exclude=auth.json -C "$HOME/.pi" agent
  git init -qb main
  git remote add origin "$REPO"
fi
git fetch -q origin main
git checkout -f -B main origin/main

# Memory stays per machine. On a fresh machine, start the knowledge base layout.
if [ ! -e memory ]; then
  mkdir -p memory/setup memory/taste memory/research
  printf -- '---\ndescription: Who the user is, goals, current focus, how to work with them\n---\n# Me\n\nKeep under 60 lines. Date each line.\n' > memory/me.md
  printf -- '---\ndescription: This machine: hardware, OS, toolchain, pi setup\n---\n# Machine\n' > memory/setup/machine.md
  printf -- '---\ndescription: Projects on this machine: path, purpose, git state, env\n---\n# Projects\n' > memory/setup/projects.md
  printf -- '---\ndescription: Dated setup decisions and gotchas\n---\n# Decisions\n' > memory/setup/decisions.md
  touch memory/inbox.md
fi

if [ -e "$HOME/.agents/skills" ] && [ ! -L "$HOME/.agents/skills" ]; then
  mv "$HOME/.agents/skills" "$HOME/.agents/skills.old"
fi
ln -sfn "$A/agents-skills" "$HOME/.agents/skills"

[ -d "$HOME/tools/vibe-wise" ] || git clone -q https://github.com/lducc/vibe-wise.git "$HOME/tools/vibe-wise"
[ -d "$HOME/tools/exp" ] || git clone -q https://github.com/lducc/exp.git "$HOME/tools/exp"
printf '#!/bin/sh\nexec python3 "$HOME/tools/exp/exp.py" "$@"\n' > "$HOME/.local/bin/exp"
chmod +x "$HOME/.local/bin/exp"

for d in extensions/*/; do
  [ -f "$d/package.json" ] && (cd "$d" && npm install --silent)
done

command pi update --extensions
patches/apply.sh

RC="$HOME/.$(basename "$SHELL")rc"
grep -q "pi-shell.sh" "$RC" || echo '. ~/.pi/agent/patches/pi-shell.sh' >> "$RC"
echo "Done. Open a new shell, run pi, and ask it to fill memory/me.md and memory/setup/ for this machine."
