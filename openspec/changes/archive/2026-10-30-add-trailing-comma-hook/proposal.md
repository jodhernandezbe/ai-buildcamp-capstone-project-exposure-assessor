## Why

Calls, signatures and collection literals that wrap across lines are inconsistently
terminated: some end with a trailing comma, some do not. Without the comma, adding an
argument or item rewrites the previous line too (noisy diffs), and `ruff format` collapses
the construct back onto one long line instead of keeping one element per line.

## What Changes

- Add a pre-commit hook that appends a trailing comma to multi-line function calls and
  definitions, method calls, lists, tuples, sets, dicts, subscripts and `with`/import
  groups in Python files.
- The hook rewrites files in place, runs only on the Python files staged for the commit
  (the edited ones), and runs before `ruff-format` so the formatter sees the commas.
- Document the convention in the root `CLAUDE.md` code-style section.
- Existing files are not bulk-rewritten; they are fixed as they are edited.

## Capabilities

### New Capabilities
- `trailing-comma-enforcement`: pre-commit behavior that adds trailing commas to multi-line
  Python constructs in edited files and cooperates with the existing formatter.

### Modified Capabilities

## Impact

- `.pre-commit-config.yaml`: new hook entry (`asottile/add-trailing-comma`) ahead of `ruff-format`.
- `CLAUDE.md`: one line in Code style (root file must stay under 80 lines).
- `tests/`: a test asserting the hook is configured and ordered before `ruff-format`.
- No runtime code, no new project dependency (the hook installs in its own pre-commit env).
