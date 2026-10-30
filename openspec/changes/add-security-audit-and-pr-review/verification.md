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
