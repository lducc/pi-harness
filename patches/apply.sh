#!/usr/bin/env bash
# Re-apply local pi package patches after `pi update`. Safe to run repeatedly.
R="$HOME/.pi/agent/git/github.com/amosblomqvist/pi-interactive-subagents"
P="$HOME/.pi/agent/patches/interactive-subagents-provider-ext.patch"
if git -C "$R" apply --reverse --check "$P" 2>/dev/null; then
  echo "subagents patch: already applied"
elif git -C "$R" apply "$P"; then
  echo "subagents patch: applied"
else
  echo "subagents patch: FAILED (upstream changed; re-make the patch)" >&2; exit 1
fi
