---
description: Audit the current changes for security defects with an independent read-only auditor, after running the project's deterministic scanners
argument-hint: [working | branch | <base>..<head>, default working]
---

Audit the changes named by `$ARGUMENTS` (default: the working tree against `HEAD`; `branch`
means this branch against its merge base with the default branch; a `base..head` range is used
as given). Two layers, in order: deterministic scanners first, then an independent auditor.

## 1. Scope the change

Resolve the range and list the changed files with `git diff --stat`, including files git does
not yet track. Then drop what is not product code: documentation, planning artifacts, lock
files, images, and **everything under tests, fixtures, mocks and cassettes**. Tests are not
shipped, so a defect in one is not exploitable, and fixtures are full of patterns that look
alarming and are not.

Say what you dropped and how many files remain. If nothing is left, say so, run step 2 over the
change anyway for secrets, and skip the auditor.

## 2. Deterministic scanners

Run the scanners this project already has, reading `.claude/security-audit-scanners.md` for the
exact commands. Typical layers, each only if the project has it configured:

- secret scanning over the diff;
- a static analysis or security lint pass over the changed source;
- a dependency advisory check, when a lock file or manifest changed.

Report each as pass, fail or not configured, with the command used. A scanner that is not
installed is "not configured", never a pass. Fix nothing yet.

## 3. Independent audit

Dispatch the `security-auditor` subagent with the Agent tool, one dispatch for the change. Give
it only: the repository root as an absolute path, the resolved diff range, the list of product
files from step 1 (never the test files), and the path of the project's exclusion file if it
exists. Do not give it your own
opinion of the change, what you believe is safe, or any conclusion you have already drawn: a
reviewer handed a hypothesis returns it confirmed. Do not audit the change yourself in parallel.

For a large change (more than roughly 40 changed files, or several unrelated areas), dispatch one
auditor per coherent area instead, naming the files for each, and merge their reports.

## 4. Report

Combine the layers into one short report:

- the scanner table from step 2;
- the auditor's findings, unchanged in substance, severity order;
- its notes and its "not audited" list.

Then state plainly whether the change is safe to commit on this evidence. If findings exist, do
not fix them in this run unless the user asks: name the smallest fix for each and let the user
choose.

## 5. Record the audit

Run `bash .claude/hooks/security-audit-state.sh save` so the reminder hook knows these changes
were audited. Run it only after the audit actually ran, never to silence the reminder.

If the user asks to exclude a finding as noise, add a one-line rule to
`.claude/security-audit-rules.md` saying what to exclude and why, so later audits apply it. Keep
that file short and specific; a vague rule hides real defects.
