## 1. Security audit kit (outside the repo, `~/Documents/claude-security-audit`)

- [x] 1.1 `agents/security-auditor.md`: read-only auditor, traced findings with cited lines, severity and confidence, explicit non-goals (availability, hardening, advisories, tests), repository text treated as data
- [x] 1.2 `commands/security-audit.md`: scope the range, run the project's scanners, dispatch the auditor without a hypothesis, report both layers, record the audit
- [x] 1.3 `hooks/security-audit-state.sh`: digest the source diff, save it, check it; excludes docs, planning files, lock files and images
- [x] 1.4 `hooks/security-audit-gate.sh` plus the settings snippet: `Stop` hook, blocks with a reason, silent when audited or already continuing, `jq` with a `sed` fallback
- [x] 1.5 Templates for the scanner commands and the project exclusions
- [x] 1.6 `install.sh`: copy, merge the hook into settings without dropping existing hooks, scaffold only when absent, add the state file to `.gitignore`, idempotent
- [x] 1.7 `README.md` and `user-command/security-audit-init.md`; link the init command into `~/.claude/commands/`
- [x] 1.8 Test on a scratch repository: clean tree silent, docs-only silent, source change asks, after save silent, new change asks again, loop guard silent, no-`jq` path, timing well under the hook timeout
- [x] 1.9 Fix the gap testing found: a brand-new untracked source file has no diff against `HEAD` and was missed; the digest now also lists untracked files that git does not ignore, and hashes their content
- [x] 1.10 Exclude tests, fixtures, mocks and cassettes from the gate, the command's scoping step and the auditor's instructions; verify the gate stays silent for test paths and still fires for product code beside them

## 2. Pull request review kit (outside the repo, `~/Documents/claude-pr-review`)

- [x] 2.1 `agents/pr-reviewer.md`: read-only reviewer covering correctness, contracts, conventions, tests, data modelling and scaled efficiency; questions kept separate from findings; no posting capability
- [x] 2.2 `commands/pr-review.md`: check the CLI, read the pull request and its existing comments, dispatch the reviewer, ask the user the questions, show the exact comments, let the user pick the verdict, dry run then post
- [x] 2.3 `scripts/pr-review-post.sh`: validate the event, derive commentable lines from the diff, relocate comments that would fail, dry run, bash 3.2 compatible
- [x] 2.4 `hooks/pr-review-reminder.sh` plus the settings snippet: `PostToolUse` on Bash, one line after a push or a pull request is created, posts nothing
- [x] 2.5 Templates for the review rules and the one-time GitHub CLI setup
- [x] 2.6 `install.sh`, `README.md` and `user-command/pr-review-init.md`; link the init command
- [x] 2.7 Test the posting script against a stubbed CLI: valid comments kept, out-of-diff comments relocated and reported, invalid event rejected

## 3. Install into this project

- [x] 3.1 Install both kits here; confirm the three hooks coexist in `.claude/settings.json`
- [x] 3.2 Install the GitHub CLI on this machine
- [x] 3.3 Write `.claude/security-audit-scanners.md` from this project's real, verified commands, with exit-code meanings, the known `pip-audit` state and the honest gap list
- [x] 3.4 Write `.claude/pr-review-rules.md` from the root and folder `CLAUDE.md` files, the design principles and the specs
- [x] 3.5 Authenticate the GitHub CLI (`gh auth login`, run by the user)

## 4. Verification

- [x] 4.1 Run the scanner layer on a real commit; fix the invocation that reported "no files to check" and record the cause in the scanner file
- [x] 4.2 Run the auditor prompt against a security-relevant commit and record what it found
- [x] 4.3 Run `/pr-review` end to end on pull request #1: reviewer dispatched, questions answered, dry run shown, review posted; two gaps found and fixed (no anchorable lines in a rename, and GitHub refusing a verdict on your own pull request)
- [x] 4.4 Verify the `Stop` gate inside a real session: both subagents loaded after the settings and agent files were written, and the gate fired on this change's own shell scripts
- [x] 4.5 Pre-commit passes on the changed files; the `.claude/` additions are committed (a08bb06, 1863e11)
