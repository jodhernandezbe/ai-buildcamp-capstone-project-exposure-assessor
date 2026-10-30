## Context

See proposal.md for motivation. What shapes the approach:

- The project already runs detect-secrets, bandit, pip-audit and `npm audit`, through pre-commit
  or by hand. Nothing ties them to a change, and `pip-audit` currently reports advisories in 14
  transitive development dependencies, so a naive report would be noise on every run.
- `.claude/` already holds the ui-craft skill, two commands and a `PostToolUse` hook, and
  `settings.json` exists. Anything added must coexist.
- The repository has a GitHub remote. `gh` was not installed on this machine before this change.
- This session's shell is zsh, which does not word-split an unquoted variable. A scanner
  invocation written for bash silently receives one argument and reports that it checked
  nothing.
- The pattern for reusable workflows is set by `~/Documents/claude-ui-craft`: a kit outside the
  repository, an installer that copies into `.claude/`, and a user-level init command.

## Goals / Non-Goals

**Goals:** an audit and a review that the author's agent cannot influence; a gate that makes the
audit the default rather than a thing to remember; posting that a human authorises; two kits
reusable in any project.

**Non-Goals:** no CI integration; no merging; no automatic fixing of findings; no new
dependency; no change to application code. The two workflows stay separate and do not report
each other's findings.

## Decisions

1. **Two kits, not one.** Exploitability and correctness need different standards of proof,
   different exclusions and different verdicts. Merging them would produce a single long report
   where the severe item hides among the nits. Each has its own agent, command, rules file and
   trigger.

2. **Subagents for both reviewers, rather than a skill.** A subagent gets its own context, which
   is the mechanism that makes independence real: it cannot see the reasoning that produced the
   change. Both prompts forbid writing, running and network access, and both commands forbid
   passing a hypothesis along with the dispatch.

3. **A `Stop` hook for the audit, a `PostToolUse` hook for the review.** The audit should cover
   a whole piece of work, so it fires once when the turn ends rather than on every edit. The
   review reminder belongs to the moment a branch is pushed or a pull request opened, which is a
   Bash call. Neither hook runs a scan: a hook that scans would delay the prompt.

4. **A digest of the source diff as audit state.** The gate must know what has already been
   audited. It hashes the diff of source files (excluding docs, planning artifacts, lock files
   and images) and compares with a recorded digest, so any further change re-arms it. The state
   lives in `.claude/.security-audit-state` and is git-ignored: it describes a working tree, not
   the project. Alternative: a marker commit or a timestamp; rejected because both go stale
   against an amended or reverted change.

5. **The gate blocks with a reason rather than printing a note.** A `Stop` hook returning
   `decision: block` continues the turn with an instruction, which is what makes the audit
   automatic rather than advisory. The `stop_hook_active` guard prevents a loop, and the state
   file stops it re-arming on an unchanged diff.

6. **Scanner commands live in a project file, verified, with an explicit gap list.** The command
   reads `.claude/security-audit-scanners.md` rather than guessing, every command there was run
   once before being written down, and the known state of `pip-audit` is recorded so the audit
   reports whether the change made it worse instead of re-listing 14 packages. The file also
   says that "Skipped" is not a pass, because that is exactly how the zsh word-splitting problem
   presents.

7. **Posting goes through a shell script, not raw `gh` calls from the model.** The script
   validates the event, derives the set of commentable lines from the diff and relocates any
   comment that would 422, so a finding is never lost to an API error. It supports a dry run so
   the user sees the exact payload. It is written for bash 3.2, the only bash on this machine, so
   it avoids `mapfile`.

8. **Approval is a user choice, enforced in the command.** The command must present the verdict
   as a question and may never select approval itself. This is the one place where being helpful
   would be wrong: an approval is a signature.

## Risks / Trade-offs

- [The gate becomes something to dismiss] → it fires once per turn, ignores non-source changes,
  and goes quiet as soon as an audit is recorded. If it still annoys, one settings entry removes
  it.
- [An audit is recorded without really running] → the state script is only ever called by the
  command's last step, and the command says not to call it to silence the reminder. A determined
  user can still bypass it; the gate is a default, not a control.
- [The auditor misses what a scanner would have caught, or the reverse] → the layers are
  explicitly divided: advisories belong to the scanner, intent belongs to the auditor.
- [Prompt injection from repository or pull request content] → both prompts treat repository and
  pull request text as data and name attempts to steer them as grounds for suspicion. This is
  mitigation, not a guarantee: neither agent should be pointed at untrusted code.
- [A review posted from the wrong account] → posting is attributed to whoever ran `gh auth
  login` on that machine; the setup note says so and the command shows the repository and pull
  request before sending.
- [Subagents are not available in the session that installs them] → both init commands say so
  up front, since the failure otherwise looks like a broken install.

## Migration Plan

Additive. Install both kits, fill the two rules files and the scanner file, restart the session,
then run each workflow once. Rollback is deleting the added files and the two `settings.json`
entries.
