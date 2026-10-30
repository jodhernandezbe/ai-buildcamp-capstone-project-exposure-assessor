#!/usr/bin/env bash
# PostToolUse hook: after Edit/Write/MultiEdit of a UI source file, remind the agent to run
# /ui-check. Reads the tool payload from stdin, prints JSON additionalContext only for files under
# the UI source directory with a UI extension, and always exits 0. Never starts anything.
#
# Usage in settings.json: bash "$CLAUDE_PROJECT_DIR/.claude/hooks/ui-reminder.sh" frontend/src
set -u

UI_DIR="${1:-frontend/src}"
UI_DIR="${UI_DIR%/}"
payload="$(cat 2>/dev/null || true)"

if command -v jq >/dev/null 2>&1; then
  path="$(printf '%s' "$payload" | jq -r '.tool_input.file_path // empty' 2>/dev/null || true)"
else
  path="$(printf '%s' "$payload" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)"
fi

[ -n "$path" ] || exit 0

case "$path" in
  *.tsx|*.jsx|*.css) ;;
  *) exit 0 ;;
esac

case "$path" in
  "$UI_DIR"/*|*/"$UI_DIR"/*) ;;
  *) exit 0 ;;
esac

printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"UI source changed (%s). Before calling this work done, run /ui-check for the surface you changed and follow DESIGN.md."}}\n' "${path##*/}"
exit 0
