# Exposure Assessor

LangChain/LangGraph agent that produces screening-level chemical exposure and risk
assessments. Python 3.13, managed with uv.

## Commands

    uv sync                # install deps
    uv run pytest          # tests
    uv run ruff format .   # format (run before every commit)
    uv run ruff check .    # lint
    uv run pyright         # strict type check
    uv run bandit -c pyproject.toml -r agent models prompts tools   # security lint

Test, format, lint, pyright and bandit must pass before work is considered done.
Pre-commit enforces them (`uv run pre-commit run --all-files`). Never bypass with
`--no-verify`; never put secrets in code (detect-secrets guards `.secrets.baseline`).

## Layout and boundaries

- `models/`  pure deterministic NumPy equations; physical units in every docstring.
- `agent/`   orchestration only: graph wiring, state, model calls.
- `tools/`   tool logic only, grouped by concern (`informatics/`, `emissions/`,
  `geospatial/`, `exposure/`). One module per tool group.
- `prompts/` Markdown prompt files plus `registry.py` to load them.
- `tests/`   pytest suite mirroring the package layout (`tests/tools/emissions/test_stack.py` tests `tools/emissions/stack.py`). Every test directory needs an `__init__.py`.

Dependency direction: `agent` -> `tools` -> `models`; `agent` -> `prompts`. Never the reverse.

### Model rules
- `models/` must not import langchain, langgraph, `tools`, `agent`, or `prompts`, and
  must not do I/O. Functions are pure and deterministic; validate inputs with `ValueError`.
- State units explicitly (e.g. g/s, mg/m^3, mg/(kg*day)) in every docstring.

### Agent rules
- `agent/` must stay provider-agnostic: accept a `BaseChatModel` by injection.
  Never import `langchain_openai`, `langchain_anthropic`, etc. in `agent/`, `tools/`,
  or `prompts/`.
- Do not put domain or calculation logic in `agent/`. If the agent needs a
  capability, add a tool.
- The agent reads tools only via `tools.registry`.

### Tool rules
- Tools must not import from `agent/`, and must not call an LLM.
- Tools must not import other tool subfolders; shared types go in `tools/schemas.py`.
- Every tool uses `@tool`, has full type hints on inputs and outputs (TypedDicts,
  not bare `dict`), and a rich docstring: purpose, `Args:`, `Returns:` with units.
  The docstring is what the LLM sees, so keep it accurate.
- New tools are added to the folder's `TOOLS` list and `tools/registry.py`, and
  to `tests/tools/test_registry.py` and add a test under the tool's folder in `tests/tools/`.

### Prompt rules
- Prompts live in `prompts/*.md`. Never inline prompt text in Python.
- Load prompts through `prompts.registry.load_prompt`.
- Structure prompts with XML tags (`<role>`, `<context>`, `<instructions>`,
  `<output_format>`).

## Code style

- Every Python file starts (after the docstring) with `from __future__ import annotations`.
- Strict static typing: annotate all functions; no untyped `dict`, no `Any` unless unavoidable.
- Formatting and linting are enforced by ruff (config in `pyproject.toml`); do not
  hand-format or add `# noqa` without a reason.
- Never invent numeric values in tool stubs or tests that look like real data.

## Secrets

`.env` holds API keys and is git-ignored. Never commit it or print its contents.
