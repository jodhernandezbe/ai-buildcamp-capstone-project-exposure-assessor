#!/usr/bin/env bash
# Stop hook: when the turn ends with source changes that have not been audited, tell Claude to
# run the independent audit before finishing. Reads the Stop payload on stdin; always exits 0.
#
# Guards against looping: stop_hook_active true means Claude is already continuing because of a
# stop hook, so this one stays silent.
set -u

ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
STATE_SH="$ROOT/.claude/hooks/security-audit-state.sh"
payload="$(cat 2>/dev/null || true)"

active=""
if command -v jq >/dev/null 2>&1; then
  active="$(printf '%s' "$payload" | jq -r '.stop_hook_active // false' 2>/dev/null || true)"
else
  printf '%s' "$payload" | grep -q '"stop_hook_active"[[:space:]]*:[[:space:]]*true' && active="true"
fi
[ "$active" = "true" ] && exit 0

[ -x "$STATE_SH" ] || exit 0
bash "$STATE_SH" check && exit 0

printf '{"decision":"block","reason":"Source files changed in this turn and have not been security audited. Run /security-audit before finishing: deterministic scanners first, then the independent security-auditor subagent on the diff. Report what it found (including nothing found), then record it with the state script. If the user has told you to skip the audit, say so plainly and stop."}\n'
exit 0
