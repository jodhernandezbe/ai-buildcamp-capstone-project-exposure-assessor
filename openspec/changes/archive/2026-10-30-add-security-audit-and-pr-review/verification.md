# Verification, 2026-10-30

## Security audit workflow

### Gate (`Stop` hook), on a scratch repository

| Case | Expected | Result |
| --- | --- | --- |
| Clean tree | silent | silent |
| Documentation only changed | silent | silent |
| Tracked source file edited, unaudited | asks for the audit | asks |
| After the audit is recorded | silent | silent |
| Further edit after recording | asks again | asks |
| `stop_hook_active` true | silent (no loop) | silent |
| `jq` absent | still correct via the text fallback | silent |
| Brand-new untracked source file | asks | **missed, then fixed** |
| Git-ignored file only | silent | silent |
| Test files (`tests/`, `test_*.py`, `conftest.py`, `__tests__/`, `*.test.tsx`) | silent | silent |
| Product file alongside tests | asks | asks |
| Run time | well under the 15 s timeout | 54 ms |

Two defects were found by testing and fixed:

1. **Untracked files were invisible.** The digest only read `git diff HEAD`, so a brand-new
   module, the commonest way new code arrives, never triggered the gate. It now also lists
   untracked files git does not ignore and hashes their content.
2. **Tests triggered the gate.** Excluded at the user's request, in the digest, in the command's
   scoping step and in the auditor's own instructions: a test is not shipped, so a defect in one
   is not exploitable, and fixtures contain patterns that look alarming and are not.

### Scanner layer, on commit `cc54747` (Logfire monitoring)

| Layer | Result |
| --- | --- |
| Secrets (detect-secrets over the changed files) | pass |
| Security lint (bandit over the changed packages) | pass, no issues |
| Dependency advisories (pip-audit) | 14 packages, all transitive development dependencies |
| Frontend advisories (npm audit, high) | 0 |

One defect found and fixed: the documented secrets command used `--files $FILES`, which
word-splits in bash but not in zsh. The whole list arrived as a single argument and pre-commit
reported "no files to check" while appearing to pass. The command now pipes the paths through
`xargs`, and the scanner file states that "Skipped" is never a pass.

### Independent auditor, on the same commit

Dispatched with the repository root, the range, the backend file list and the exclusions file,
and no hypothesis about the change. Verdict: **no findings**, with the reasoning for each path it
closed rather than a bare assertion. It traced the SQL interpolation to a doubly-constrained
identifier, confirmed the read token never leaves the server, read the installed scrubber's
source to check what redaction actually restores, checked the new routes sit behind the existing
origin guard, and confirmed two moved modules were byte-identical relocations.

It raised five notes below the reporting bar. The most useful is a latent one: a telemetry
client binds to the global tracer provider, so if telemetry were ever configured in the wrong
order, prompts and tool input could be exported to a third-party endpoint with no scrubbing. No
shipped entry point reaches it, which is why it is a note and not a finding. **This is the class
of defect the scanners cannot reach**: nothing is syntactically dangerous, and the problem is an
ordering assumption across three files.

Open: the gate has not yet been observed inside a real session, because subagents and the
settings hook are loaded at session start.

## Pull request review workflow

### Posting script

| Case | Result |
| --- | --- |
| Comment on an added line | kept inline |
| Comment on a context line (`RIGHT`) | kept inline |
| Comment on a removed line (`LEFT`) | kept inline |
| Comment on a line outside the diff | moved into the review body and reported |
| Comment on a file not in the diff | moved into the review body and reported |
| Review event other than the three allowed | rejected, nothing sent |
| Payload file missing | rejected with the path |
| GitHub CLI not authenticated | stops with the setup instructions |
| Dry run | prints the exact payload, sends nothing |

The script was written for bash 3.2, the only bash on this machine, after an initial version
used `mapfile` (bash 4+).

Open: no end-to-end review against a real pull request yet. It needs `gh auth login`, which only
the user can complete, and an open pull request on the repository.

### End-to-end on a real pull request (#1, a README rename)

Run after the user authenticated the GitHub CLI. The reviewer subagent was dispatched with the
pull request's refs, files, title and body and the project rules, and with no reading of the
change from the dispatching session.

It returned two blocking findings, both caused by the rename rather than by the file's content:
`pyproject.toml` still declares `readme = "README.md"`, so a metadata build would fail; and
GitHub renders a landing-page README only for canonical names, so the repository front page
would show no README at all. It raised four questions, two of which were put to the user and
answered before any comment text was drafted. It correctly reported that the diff contains no
changed content lines, so no finding could anchor inline.

Posted as review 5711183240.

Two things this run established that testing against a stub could not:

1. **A pure rename has zero commentable lines.** The posting script's line check derived an empty
   set from the diff, which is correct: a 100% similarity rename produces no hunks. The findings
   went in the review body.
2. **GitHub refuses a verdict on your own pull request.** `REQUEST_CHANGES` came back 422 with
   "Can not request changes on your own pull request". The script now compares the author with
   the authenticated account and stops before sending, naming the comment fallback; the command
   presents the restriction before the user picks a verdict; the README and the setup note say
   so. The findings were posted as a comment with the intended verdict stated in the body.
