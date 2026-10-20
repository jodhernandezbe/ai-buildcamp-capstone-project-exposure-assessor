## Why

Every tool and model is unit-tested, but nothing tests what the agent *does*: whether an LLM
driving the tools calls the right ones in the right order, keeps their quality signals, and
reports only numbers the tools produced. The agent's decisions live in the tool descriptions
and the system prompt, so a reworded description can silently break the assessment chain.
A repeatable behavioral evaluation, run against an OpenAI chat model with a professional
evaluation framework (Evidently), makes those regressions visible.

## What Changes

- New `evals/` package: an evaluation harness that runs the real agent graph with an OpenAI
  chat model on scripted scenarios and turns each run into one row (query, tool calls with
  arguments, tool outputs, final report, error).
- Recorded tool outputs ("cassettes"): network tools are recorded once from the live
  services and replayed afterwards, so runs are cheap and repeatable and no tool output is
  invented. Offline tools (the exposure calculation) run for real. A call with no recording
  fails closed and is reported.
- Evidently scores the rows: deterministic checks (tool trajectory, call counts, arguments,
  completion) as custom descriptors with pass/fail tests, and OpenAI LLM judges for report
  qualities that code cannot check. Each run writes an Evidently HTML report.
- A scenario catalogue covering the brainstormed cases (happy paths, tool order and
  fallbacks, edge cases, failure modes); scenarios are added one at a time. The first
  implemented scenario is the full assessment of a facility that has its own NEI stacks.
- Pytest entry point under an `eval` marker, excluded from the default run and pre-commit
  (it needs the OpenAI key and costs tokens), like the existing `smoke` marker.
- `[evaluation]` settings: agent and judge model names, API-key variable, timeouts,
  recursion limit for eval runs, cassette and report paths.
- New dependency: `evidently`.

Out of scope (a separate change, prerequisite for three catalogued scenarios): the graph's
default recursion limit, a warning when TRI cannot be read, and the meteorology year
fallback. Those scenarios are catalogued as blocked until it lands.

## Capabilities

### New Capabilities
- `agent-evaluation`: behavioral evaluation of the agent — harness, cassette record/replay,
  Evidently scoring (deterministic descriptors and LLM judges), scenario catalogue, report
  output and the opt-in pytest entry point.

### Modified Capabilities
- `app-configuration`: adds the `[evaluation]` settings section and its typed loader.

## Impact

- New: `evals/` (runner, cassettes, scenarios, descriptors), `config/evaluation.py`,
  `tests/evals/`, `evals/CLAUDE.md`.
- Changed: `config/settings.toml`, `pyproject.toml` (dependency, `eval` marker, default
  `addopts`), `.pre-commit-config.yaml` and root `CLAUDE.md` (the new layer in function-length,
  pyright and bandit checks), `.gitignore` (generated reports).
- No change to `agent/`, `tools/`, `models/` or `prompts/` behavior.
- Running evals needs `OPENAI_API_KEY`; recording cassettes also needs the CompTox and
  Census keys and network access.
