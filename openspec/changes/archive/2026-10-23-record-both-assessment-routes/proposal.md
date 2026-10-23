## Why

The scenario for CAS 96-12-8 fails intermittently with "unrecorded call": the agent may assess
the facilities by the batch tool `assess_facilities` or by calling the per-facility tools by
hand, and the cassette holds only the by-hand route. The earlier decision was that the route
must not matter to the evaluation. Four of four runs failed on the same day the unchanged code
had passed before, so the route the model picks drifts and the cassette has to cover both.

## What Changes

- A scenario can list extra calls, made once when recording, so the cassette also holds routes
  the agent did not take in the recording run (here `assess_facilities` for the scenario's CAS).
- Recording can add to an existing cassette instead of replacing it: a new command
  `python -m evals record-extra <scenario>` makes only the scenario's extra calls (no agent run)
  and merges them with what the cassette already holds.
- `record <scenario>` also makes the extra calls after the agent run.
- The full-assessment scenario lists `assess_facilities` for CAS 96-12-8, and its cassette is
  re-recorded with it.

Out of scope: changing the checks (they already read the batch output and cover either route),
the prompt, or any tool description.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `agent-evaluation`: recordings can cover routes the agent did not take, and be extended without
  a new agent run.

## Impact

- `evals/cassette.py` (seed a recorder from an existing file), `evals/scenarios.py` (extra
  calls), `evals/suite.py` and `evals/__main__.py` (record them, new command), the cassette
  `evals/cassettes/full-assessment-with-nei-stacks.json`, `evals/CLAUDE.md`.
- Tests under `tests/evals/`. One live recording run (network).
