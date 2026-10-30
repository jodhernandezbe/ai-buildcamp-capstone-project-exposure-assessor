## Why

Security review and pull request review both depend today on someone remembering to ask for
them, and on the same agent that wrote the code judging its own work. A model asked to review
its own diff rates its own work, and a reviewer handed a conclusion returns it confirmed. The
project already has deterministic scanners (detect-secrets, bandit, pip-audit, npm audit) but
nothing ties them to a change, and nothing covers the defect classes no rule expresses: a
missing authorisation check, a trust boundary crossed, a token reaching a log. The same gap
exists for ordinary review: nothing anchors a comment to a project rule, and nothing carries a
reviewer's questions to a human before they become public comments.

## What Changes

Two independent workflows, each installed into `.claude/` and committed so every colleague gets
it by cloning. They are deliberately separate: one judges exploitability, the other judges
correctness and conventions, and neither reports the other's findings.

**Security audit**
- `security-auditor` subagent: read-only, separate context, audits a diff and must trace input,
  dangerous operation and missing check to a cited line before reporting anything.
- `/security-audit [working|branch|<range>]`: runs the project's deterministic scanners first,
  then dispatches the auditor, then reports both layers and records that the diff was audited.
- A `Stop` hook that, when a turn ends with source changes nobody has audited, asks for the
  audit before the turn finishes. It ignores documentation, planning files, lock files and
  images, stays silent on an already-audited diff, and never loops.
- `.claude/security-audit-scanners.md` (the project's verified scanner commands and its honest
  list of gaps) and `.claude/security-audit-rules.md` (exclusions, each with a reason).

**Pull request review**
- `pr-reviewer` subagent: read-only, reports findings anchored to `file:line` with a concrete
  failure, cites a project rule rather than taste, and raises at most five questions.
- `/pr-review [number]`: reads the pull request with `gh`, dispatches the reviewer, puts its
  questions to the user, shows the exact comments, then posts and optionally approves.
- `.claude/scripts/pr-review-post.sh`: posts through `gh`, rejecting an invalid review event and
  moving any comment that does not anchor to a diff line into the review body instead of failing.
- A `PostToolUse` hook that mentions `/pr-review` after a push or `gh pr create`, and posts
  nothing itself.
- `.claude/pr-review-rules.md` (what matters here, what not to comment on, who may approve) and
  `.claude/pr-review-gh-setup.md` (the one-time GitHub CLI setup each reviewer does).

Approval and comments are never the agent's decision: the user chooses the verdict in the turn,
after seeing the exact payload.

## Capabilities

### New Capabilities
- `security-audit-workflow`: an independent audit of every change, layered over the project's
  deterministic scanners, with a gate that asks for it before a turn ends.
- `pull-request-review-workflow`: an independent review of a pull request that asks the author's
  questions first and posts only what a human approved.

### Modified Capabilities
- (none)

## Impact

- New: `.claude/agents/{security-auditor,pr-reviewer}.md`,
  `.claude/commands/{security-audit,pr-review}.md`,
  `.claude/hooks/{security-audit-gate,security-audit-state,pr-review-reminder}.sh`,
  `.claude/scripts/pr-review-post.sh`, four project config files, a `.gitignore` line for the
  per-working-tree audit state.
- Edited: `.claude/settings.json` gains a `Stop` hook and a second `PostToolUse` entry alongside
  the existing UI reminder.
- No application code, no dependency, no CI change. `gh` is required only to post a review.
- Reusable kits live outside the repository at `~/Documents/claude-security-audit` and
  `~/Documents/claude-pr-review`, each with an installer and an init command, following the
  pattern already set by `~/Documents/claude-ui-craft`.
