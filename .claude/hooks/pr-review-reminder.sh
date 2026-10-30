#!/usr/bin/env bash
# PostToolUse hook: after a push or a pull request is created from the command line, remind the
# agent that /pr-review exists. Reads the tool payload on stdin, prints at most one line, and
# always exits 0. It never runs gh itself.
set -u

payload="$(cat 2>/dev/null || true)"

if command -v jq >/dev/null 2>&1; then
  cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"
else
  cmd="$(printf '%s' "$payload" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)"
fi
[ -n "$cmd" ] || exit 0

case "$cmd" in
  *"gh pr create"*) what="A pull request was just created." ;;
  *"git push"*)     what="A branch was just pushed." ;;
  *) exit 0 ;;
esac

printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"%s Offer /pr-review to review it with the independent reviewer, ask the user about anything suspicious, and post the comments. Do not run it or post anything without the user asking."}}\n' "$what"
exit 0
