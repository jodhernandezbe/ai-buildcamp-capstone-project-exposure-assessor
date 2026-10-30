## Context

`ruff-format` (line length 100) honors the "magic trailing comma": a bracketed construct
ending in a comma stays one element per line, otherwise it is joined if it fits. Ruff lint
here selects `E, F, I, UP, B, FA, ANN`, so rule `COM812` is not active. Pre-commit already
passes staged filenames to hooks, so "edited files only" comes for free.

## Goals / Non-Goals

**Goals:** auto-add trailing commas on edited Python files; stable alongside `ruff-format`;
no new project dependency.
**Non-Goals:** reformatting untouched files; enforcing commas on single-line constructs;
changing line length.

## Decisions

- **Use `asottile/add-trailing-comma`** as a remote pre-commit hook. It is a fixer
  (rewrites files, exits non-zero when it changed something), matching the user's ask to
  "add the comma", and it covers calls, defs, literals, subscripts and imports.
  - *Alternative: ruff `COM812` + `--fix`.* Rejected: ruff documents COM812 as conflicting
    with the formatter and it requires an ignore dance; two sources of truth.
  - *Alternative: custom script like `check_function_length.py`.* Rejected: reimplementing
    a tokenizer-level rewrite is more code to own than a pinned hook.
- **Order: before `ruff` and `ruff-format`.** Commas are added first so the formatter keeps
  the one-per-line layout; `ruff-format` then normalizes spacing. Placed in its own repo block
  between the pre-commit-hooks block and the ruff block.
- **Scope:** default `types: [python]`; no `files` filter, so it also covers `tests/` and
  `scripts/`, which ruff already formats.
- **Pin `rev` to the latest release** found with `pre-commit autoupdate`, not a value
  copied from memory.
- **Docs:** one line in `CLAUDE.md` Code style; root file stays under 80 lines.

## Risks / Trade-offs

- Hook may disagree with ruff-format on an edge case and loop → verify with a second
  `pre-commit run --all-files` pass producing no diff; if a construct oscillates, leave it
  as a single line.
- Comma-expanded constructs add lines, so an edited function may exceed the 18-line limit and fail
  `function-length` → accepted (option chosen with the user); the editor splits the function into
  helpers as part of that commit. Never bulk-run `--all-files` expecting a clean tree.
- First commit touching an old file includes comma-only diff noise → accepted; scoped to edited files.
- Needs network on first `pre-commit install` to fetch the hook → same as the other remote hooks.
