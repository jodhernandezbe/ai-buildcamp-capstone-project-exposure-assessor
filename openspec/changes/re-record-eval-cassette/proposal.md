## Why

The eval cassette `full-assessment-with-nei-stacks.json` was recorded on 2026-10-21 at 07:41,
before `fetch_stack_parameters_from_nei` took `eis_ids` and before `assess_facilities` existed.
A replay now hits unrecorded calls on either route the agent takes, so `uv run pytest -m eval`
fails on "no unrecorded call" at HEAD. It could not be re-recorded the same day: the TLS
certificate of `comptox.epa.gov` expired at 23:59 GMT on 2026-10-21, so every CompTox request
fails and a recording made then would carry no benchmarks. Meanwhile the scenario was evaluated
with CompTox replayed from the committed cassette and every other tool live (13 scored runs:
9 pass; every deterministic check passed in all 13; the 4 failures are the report judge, three
of them because the report did not name the weather source).

## What Changes

- Re-record the cassette once CompTox answers again, on a run that covers the calls of both
  routes (the batch assessment, and the chain by hand), and run `uv run pytest -m eval` three
  times.
- Nothing in the code changes; this change carries the one verification step the three
  archived changes (`refactor-workspace-layout`, `naics-titles-and-full-coverage`,
  `batch-facility-assessment`) could not finish.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `agent-evaluation`: a cassette must hold a recording for every call the agent can make on
  either route, and a replay that hits an unrecorded call means the scenario is re-recorded.

## Impact

- `evals/cassettes/full-assessment-with-nei-stacks.json` (re-recorded live; never edited by hand).
- Costs OpenAI tokens (agent and judge) and needs the CompTox and Census keys.
