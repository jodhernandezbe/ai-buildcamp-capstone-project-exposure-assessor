# Exposure Assessor

LangChain/LangGraph agent that produces screening-level chemical exposure and risk
assessments. Python 3.13, managed with uv.

## Commands

    uv sync                # install deps
    uv run pytest          # tests
    uv run ruff format .   # format (run before every commit)
    uv run ruff check .    # lint
    uv run pyright         # strict type check
    uv run bandit -c pyproject.toml -r agent commons config models prompts tools   # security lint
    uv run python scripts/check_function_length.py --max 18 $(git ls-files 'agent/*.py' 'commons/*.py' 'config/*.py' 'models/*.py' 'prompts/*.py' 'tools/*.py')   # function length

Test, format, lint, pyright, bandit and the function-length check must pass before work is considered done.
Pre-commit enforces them (`uv run pre-commit run --all-files`). Never bypass with
`--no-verify`; never put secrets in code (detect-secrets guards `.secrets.baseline`).

## Layout and boundaries

- `models/`  pure deterministic NumPy equations; physical units in every docstring.
- `agent/`   orchestration only: graph wiring, state, model calls.
- `tools/`   tool logic only, grouped by concern (`informatics/`, `emissions/`,
  `geospatial/`, `exposure/`). One module per tool group.
- `prompts/` Markdown prompt files plus `registry.py` to load them.
- `config/`  `settings.toml` plus a typed loader (`loader.py`) for external-service URLs,
  endpoints and timing. Never hard-code URLs or endpoints in Python; add them here.
- `commons/` small, generic, pure utilities used across layers (e.g. `units.py`, Pint-based
  unit conversion). No project knowledge, no I/O, no config reads: callers pass in what they need.
- `tests/`   pytest suite mirroring the package layout (`tests/tools/emissions/test_stack.py` tests `tools/emissions/stack.py`). Every test directory needs an `__init__.py`.

Dependency direction: `agent` -> `tools` -> `models`; `agent` -> `prompts`;
`agent`/`tools`/`models` -> `commons`; `agent`/`tools` -> `config`. `commons` and `config`
import nothing from the project. Never the reverse.

## Folder-specific rules

Each layer keeps its own rules in a `CLAUDE.md` inside its folder. Claude Code loads these
automatically when working in that folder, so read and follow the one that applies before
editing there:

- `agent/CLAUDE.md`   provider-agnostic orchestration only.
- `commons/CLAUDE.md` generic pure utilities with no project imports.
- `models/CLAUDE.md`  pure deterministic equations with units in every docstring.
- `prompts/CLAUDE.md` prompt files, XML structure, loading through the registry.
- `tools/CLAUDE.md`   `@tool` conventions, registry and test requirements.

When a new layer needs rules of its own, add a `CLAUDE.md` in its folder and list it here.
Keep this root file under 80 lines (checked by `tests/test_claude_md.py`); put detail in
folder `CLAUDE.md` files or `docs/`.

## Design principles

SOLID, DRY and defensive programming apply to all code; the full rules are imported here:

@docs/design-principles.md

## Code style

- Every Python file starts (after the docstring) with `from __future__ import annotations`.
- Functions stay short: at most 18 body lines (signature, docstring, blank lines and comments
  not counted; nested functions count toward the outer one). Split long ones into small named
  helpers. Enforced by `scripts/check_function_length.py` as a pre-commit hook on the source
  packages (not `tests/`); never raise the limit or skip the hook to make code fit.
- Strict static typing: annotate all functions; no untyped `dict`, no `Any` unless unavoidable.
- Formatting and linting are enforced by ruff (config in `pyproject.toml`); do not
  hand-format or add `# noqa` without a reason.
- Never invent numeric values in tool stubs or tests that look like real data.
