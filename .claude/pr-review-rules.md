# Project review rules

Read by the `pr-reviewer` subagent and by `/pr-review`.

## What matters most in this project

1. **A value the API did not send must never be shown, computed or converted.** An absent value
   renders as "not reported" with its reason, never `0`, `-` or an empty cell. The frontend
   never does arithmetic on a scientific quantity. (`frontend/CLAUDE.md`, `web-ui-shell` spec.)
2. **Layering is one-way and declared.** `agent` → `tools` → `models`; `commons` and `config`
   import nothing from the project; nothing imports `evals` or `api`; the frontend talks to the
   system only through `/api/v1/*`. A new import that crosses a boundary is blocking.
   (root `CLAUDE.md`.)
3. **Configuration, not constants.** URLs, endpoints, units, column names, thresholds, digits
   and model names live in `config/settings.toml` and its typed loaders, and reach the frontend
   through the client settings endpoint. A literal in Python or TSX is blocking.
4. **Determinism stays in `models/`,** pure NumPy with physical units in every docstring.
   Orchestration stays in `agent/`. Tool logic stays in `tools/`, one module per tool.
5. **Types carry the meaning.** Pass and return the smallest type that works: focused TypedDicts
   and dataclasses, not one wide dict; frozen dataclasses and tuples for anything cached or
   config-backed; copies returned, never the shared object. A quantity without its unit, or a
   type that admits a state the code cannot handle, is a finding.
   (`docs/design-principles.md`, interface segregation and defensive programming.)
6. **Cost at real scale.** An external call inside a loop over facilities, stacks or tracts; a
   repeated parse or load that could happen once; a quadratic pass over the workspace. Every
   external call is time-bound, and a retry or fan-out multiplies it. Name the scale.
7. **New behaviour needs a test beside it,** mirroring the package layout under `tests/`. A new
   `@tool`, a new pure helper or a new reducer without one is blocking. Defensive rules get a
   negative test. Never invent numeric values that look like real measurements.

## Conventions a reviewer should cite

- Root `CLAUDE.md` for layout, boundaries and code style (18-line functions, strict typing,
  `from __future__ import annotations`).
- `docs/design-principles.md` for SOLID, DRY and the defensive rules (validate at the boundary,
  fail closed, setup errors raise and data problems return `None` with a warning, time-bound
  every external call, catch only expected exceptions).
- The folder `CLAUDE.md` that owns the code under review: `agent/`, `tools/`, `models/`,
  `prompts/`, `app/`, `api/`, `frontend/`, `commons/`, `evals/`.
- `frontend/DESIGN.md` for anything visual, plus `/ui-check` rather than a review comment.
- The spec in `openspec/specs/<capability>/spec.md` when the change touches declared behaviour.

## Do not comment on

- Formatting, import order, trailing commas and line length: ruff, the trailing-comma hook and
  eslint own them, and pre-commit blocks the commit anyway.
- Type annotations that pyright already accepts in strict mode. Data modelling is still fair
  game: the checker accepts a wide dict, this project does not.
- Speculative performance. Without a concrete scale from this domain, it is a question.
- Function length: the pre-commit hook enforces 18 body lines and reports the exact offender.
- Security defects: `/security-audit` owns them. Raise one as a question and say so.
- The wording of prompts in `prompts/`: they are tuned against evals, so propose an eval rather
  than an edit.

## Approval

- Approve only when nothing is blocking and every question has been answered by the author.
- Never approve a change that alters declared behaviour without the matching OpenSpec change
  (`openspec/changes/<name>/` with its specs), or that edits `openspec/specs/` by hand outside
  an archive.
- Never approve a change whose pre-commit gates have not been run: tests, ruff, pyright, bandit,
  function length and the frontend check.
- Never approve your own pull request.
