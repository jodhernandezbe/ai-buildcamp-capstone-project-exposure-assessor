## Context

`agent/graph.py` compiles a model ↔ `ToolNode` loop around an injected `BaseChatModel`; the only
agent test checks the wiring with a fake model. The nine registered tools call EPA, Census,
CompTox, ERA5 and the SCC index, except `calculate_exposure_metrics`, which is pure computation.
A nationwide TRI query can take minutes and return hundreds of facilities, so evaluations cannot
hit live services on every run. Project rules: settings live in `config/`, functions stay under 18
lines, strict typing, and only the outer edge builds concrete collaborators.

## Goals / Non-Goals

**Goals:**
- Run the production graph, prompt and tool descriptions with a real OpenAI model.
- Repeatable runs: same tool outputs every time, no hand-written data.
- Most checks deterministic; LLM judges only for report wording.
- The harness itself is unit-tested offline and runs in pre-commit; only scenario runs are opt-in.

**Non-Goals:**
- Statistical pass rates over repeated runs (one run per scenario for now).
- Production monitoring or tracing dashboards.
- Fixing agent behavior found by the scenarios (separate changes).

## Decisions

### D1. New `evals/` layer at the outer edge
`evals/` imports `agent`, `tools` and `config` and builds the OpenAI chat model; nothing imports
`evals`. This keeps `agent/` provider-agnostic: the model is still injected.
Modules: `settings` access via `config/evaluation.py`; `cassette.py` (record/replay tools);
`runner.py` (build agent, invoke, extract the record); `checks.py` (deterministic checks);
`judges.py` (judge criteria); `scoring.py` (Evidently adapter and report); `scenarios.py`
(catalogue); `__main__.py` (CLI to record a scenario or run all). It joins the function-length,
pyright and bandit gates. *Alternative:* put it under `tests/` — rejected, because the harness
and recording CLI are code with their own tests, not tests.

### D2. Evidently 0.7 scores the records
Each record becomes one row of a pandas DataFrame (scalar columns plus the record as JSON).
Deterministic checks are plain functions `record -> CheckResult(passed, reason)`; an adapter
wraps each as an Evidently `CustomDescriptor` producing a `PASS`/`FAIL` column with an
`eq("PASS")` test and a companion reason column. Judges are `BinaryClassificationLLMEval`
descriptors with provider `openai`, the judge model from settings, `include_reasoning=True`, and
an `eq(<pass category>)` test. A `TestSummary` gives the per-scenario verdict; `Report([TextEvals()])`
renders the HTML report into the configured directory. Pytest reads the scored columns and asserts,
printing failing reasons. *Alternatives:* MLflow (better LangGraph tracing) and DeepEval (pytest
native) — the user chose Evidently; since the tool-trajectory checks are custom code in any
framework, the gap is the record extraction we write in D4.

### D3. Cassettes: record from live tools, replay by matching arguments
A cassette is one JSON file per scenario: for each tool name, a list of `{args, output}` pairs.
Arguments are matched after canonicalising (keys sorted, scalar values as stripped strings), so
`frs_id` passed as an int or a string matches. Replay builds, for each network tool, a
`StructuredTool` with the original tool's `name`, `description` and `args_schema` (Liskov: the
model sees exactly the production contract) whose function looks up the output. A miss returns
`{"error": "no recording for <tool>(<args>); re-record the scenario"}` and logs the call as
unrecorded. Tools listed in `[evaluation] live_tools` (`calculate_exposure_metrics`) are passed
through unchanged. Recording mode wraps the live tools to append each output and writes the file
at the end. *Alternative:* VCR-style HTTP cassettes — rejected: tools make many paged requests
with retries, and a tool-level cassette is smaller, readable, and independent of transport.

### D4. The record is extracted from the message history
The runner invokes the graph with `{"recursion_limit": max_steps}`, catches the expected
failures (`GraphRecursionError`, OpenAI API errors) into the record's `error`, and walks the
returned messages: each `AIMessage.tool_calls` entry is paired with its `ToolMessage` by
`tool_call_id`, giving ordered `(name, args, output)` calls; the last `AIMessage` without tool
calls is the final report. Tool outputs are parsed back from JSON where possible so checks can
read fields such as `candidates`.

### D5. Scenario catalogue as frozen dataclasses
`Scenario(id, query, cassette, checks, judges, blocked=None)`. Checks are small factories, e.g.
`called_with("fetch_chemical_properties", cas_number=...)`, `once_per_candidate(...)`,
`not_called_for_facilities_with_candidates(...)`, `completed()`, `no_unrecorded()`, so new
scenarios compose them. Expected counts come from tool outputs in the record (spec: never from
numbers written into checks). Blocked scenarios carry their reason and are skipped.

### D6. First scenario and its data
`full-assessment-with-nei-stacks` asks "Assess the inhalation exposure and risk for CAS <cas>".
To keep the run bounded and the cassette small, the chemical is one whose live TRI inventory
returns only a few facilities with NEI stack candidates; it is chosen by probing TRI when
recording, and the cassette holds the untrimmed live outputs.

### D7. One chat model for the program and the evaluations
The agent's model is configured once, in `[agent]` (provider, model, key variable, timeout,
step limit), and built by `app/chat_model.py`, the only module that imports a chat provider.
The program (`uv run python -m app "<question>"`, `app/run.py`) and the evaluations both call
that factory, so an evaluation always tests the model the program runs (`gpt-4.1`, the model the
README already used). `agent/` stays provider-agnostic: the model is still injected. The judge is
configured separately in `[evaluation]` (`gpt-5.5-2026-04-23`, a different, stronger model, so
the agent does not grade itself). *Alternative:* an `agent_model` in `[evaluation]` — rejected,
because it lets the evaluated model drift from the one in production.

### D8. Opt-in marker
Pytest marker `eval`; `addopts` becomes `-m "not smoke and not eval"`. A `tests/evals/conftest.py`
loads `.env` and skips `eval` tests when the key variable from settings is empty, mirroring the
smoke conftest. Unit tests of the harness (cassette, runner with a scripted fake model, checks,
scoring adapter, settings) carry no marker and run in pre-commit.

## Risks / Trade-offs

- [LLM nondeterminism: the agent may pick different facilities or arguments between runs] →
  a small inventory makes the reachable call set small; unrecorded calls fail loudly with a
  re-record message instead of silently passing.
- [Cassettes go stale when tool outputs change shape] → re-record via the CLI; the replay
  uses the current tool contract, so a schema change surfaces as a failing scenario.
- [Judge disagreement or drift] → one narrow criterion per judge, reasoning stored in the report,
  judge model pinned.
- [Cost] → runs are opt-in and replay network tools; only model tokens are spent.
- [Evidently API churn between minor versions] → pin a compatible range and keep all Evidently
  calls inside `scoring.py`.

## Migration Plan

Additive. Install with `uv sync`; record with `uv run python -m evals record <scenario>`; run with
`uv run pytest -m eval`. Rollback is deleting `evals/` and the settings section.
