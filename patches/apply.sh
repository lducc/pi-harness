#!/usr/bin/env bash
# Re-apply local pi package patches after `pi update`. Safe to run repeatedly.
G="$HOME/.pi/agent/git/github.com"
P="$HOME/.pi/agent/patches"
status=0
apply() {
  if git -C "$1" apply --reverse --check "$2" 2>/dev/null; then
    echo "$(basename "$2"): already applied"
  elif git -C "$1" apply "$2"; then
    echo "$(basename "$2"): applied"
  else
    echo "$(basename "$2"): FAILED (upstream changed; re-make the patch)" >&2; status=1
  fi
}
apply "$G/amosblomqvist/pi-interactive-subagents" "$P/interactive-subagents-provider-ext.patch"
apply "$G/hinsencamp/pi-research-agent" "$P/research-agent-s2-key.patch"
exit $status
