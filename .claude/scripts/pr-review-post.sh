#!/usr/bin/env bash
# Post a pull request review from a JSON payload, using the GitHub CLI.
#
#   pr-review-post.sh <pr-number> <payload.json> [--dry-run]
#
# The payload is the GitHub "create a review" body:
#   {"body": "...", "event": "COMMENT|APPROVE|REQUEST_CHANGES",
#    "comments": [{"path": "...", "line": 12, "side": "RIGHT", "body": "..."}]}
#
# Before posting it checks, so a bad payload fails here rather than as a 422:
#   - gh is installed and authenticated;
#   - the payload parses and the event is one of the three allowed values;
#   - every comment's path is in the pull request's diff;
#   - every comment's line is a line that diff actually touches on the given side.
# Comments that fail the line check are reported and moved into the review body, so a finding is
# never silently dropped.
set -euo pipefail

PR="${1:-}"
PAYLOAD="${2:-}"
DRY=""
[ "${3:-}" = "--dry-run" ] && DRY="yes"

die() { printf 'pr-review-post: %s\n' "$*" >&2; exit 1; }

[ -n "$PR" ] && [ -n "$PAYLOAD" ] || die "usage: $0 <pr-number> <payload.json> [--dry-run]"
[ -f "$PAYLOAD" ] || die "payload not found: $PAYLOAD"
command -v gh >/dev/null 2>&1 || die "the GitHub CLI (gh) is not installed. See .claude/pr-review-gh-setup.md"
command -v jq >/dev/null 2>&1 || die "jq is required"
gh auth status >/dev/null 2>&1 || die "gh is not authenticated. Run: gh auth login. See .claude/pr-review-gh-setup.md"

jq -e . "$PAYLOAD" >/dev/null 2>&1 || die "payload is not valid JSON"
EVENT="$(jq -r '.event // "COMMENT"' "$PAYLOAD")"
case "$EVENT" in
  COMMENT|APPROVE|REQUEST_CHANGES) ;;
  *) die "event must be COMMENT, APPROVE or REQUEST_CHANGES (got: $EVENT)" ;;
esac

REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
DIFF="$(mktemp)"; VALID="$(mktemp)"; CLEAN="$(mktemp)"; DROPPED="$(mktemp)"
trap 'rm -f "$DIFF" "$VALID" "$CLEAN" "$DROPPED"' EXIT
gh pr diff "$PR" > "$DIFF" || die "could not read the diff of PR #$PR"

# Lines a comment may anchor to: for RIGHT, lines present in the head revision (context and
# added); for LEFT, lines present in the base (context and removed).
awk '
  /^\+\+\+ b\// { file = substr($0, 7); next }
  /^@@/ {
    match($0, /-[0-9]+/); old = substr($0, RSTART + 1, RLENGTH - 1) + 0
    match($0, /\+[0-9]+/); new = substr($0, RSTART + 1, RLENGTH - 1) + 0
    next
  }
  file == "" { next }
  /^\+/ { print file "\tRIGHT\t" new; new++; next }
  /^-/  { print file "\tLEFT\t"  old; old++; next }
  /^ /  { print file "\tRIGHT\t" new; print file "\tLEFT\t" old; new++; old++; next }
' "$DIFF" | sort -u > "$VALID"

# Split the comments into those that can be posted inline and those that cannot.
jq -r '.comments // [] | to_entries[] | "\(.key)\t\(.value.path)\t\(.value.side // "RIGHT")\t\(.value.line)"' "$PAYLOAD" |
  while IFS="$(printf '\t')" read -r idx path side line; do
    grep -qxF "$(printf '%s\t%s\t%s' "$path" "$side" "$line")" "$VALID" ||
      printf '%s\t%s:%s\n' "$idx" "$path" "$line"
  done > "$DROPPED"

if [ -s "$DROPPED" ]; then
  KEEP="$(cut -f1 "$DROPPED" | jq -R 'select(length > 0) | tonumber' | jq -s .)"
  NOTE="$(cut -f2 "$DROPPED" | sed 's/^/- /' | jq -Rs .)"
  jq --argjson drop "$KEEP" --argjson note "$NOTE" '
    .comments = [(.comments // [] | to_entries[] | select(.key as $k | $drop | index($k) | not) | .value)]
    | .body = (.body // "") + "\n\n**Not anchored to a diff line** (the line is outside this pull request'"'"'s diff):\n" + $note
  ' "$PAYLOAD" > "$CLEAN"
  printf 'pr-review-post: %s comment(s) are not on a diff line; moved into the review body:\n' "$(wc -l < "$DROPPED" | tr -d ' ')" >&2
  cut -f2 "$DROPPED" | sed 's/^/  /' >&2
else
  cp "$PAYLOAD" "$CLEAN"
fi

COUNT="$(jq '.comments | length' "$CLEAN")"
if [ -n "$DRY" ]; then
  printf 'DRY RUN: would post to %s PR #%s as %s with %s inline comment(s)\n' "$REPO" "$PR" "$EVENT" "$COUNT"
  jq . "$CLEAN"
  exit 0
fi

printf 'Posting %s to %s PR #%s with %s inline comment(s)...\n' "$EVENT" "$REPO" "$PR" "$COUNT"
gh api --method POST "repos/$REPO/pulls/$PR/reviews" --input "$CLEAN" \
  --jq '"posted review \(.id) (\(.state)) -> \(.html_url)"'
