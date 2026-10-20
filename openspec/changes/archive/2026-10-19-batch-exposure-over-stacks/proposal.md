## Why

The agent evaluation (`add-agent-evaluation`) shows that with ten NEI stack candidates the
agent runs the exposure calculation for only five or six of them and reports a "range" that is
not one. It does batch the calls in one turn as asked, so the limit is the payload: each call
repeats the weather, population and toxicity inputs, and the model stops writing after about
six. Two rounds of prompt and description wording passed one run in three. Fan-out over
candidates is deterministic work; it belongs in code, where it cannot be cut short.

## What Changes

- **BREAKING** `calculate_exposure_metrics` evaluates every candidate stack of a facility in one
  call: it takes `stacks` (a list of stack parameter dicts, as the NEI or SCC tools return them)
  instead of one `stack_params`, with the emission rate, weather, population and toxicity
  passed once. It returns one result per stack (the current per-stack result, unchanged in
  content) plus the range over the stacks (lowest and highest concentration, hazard quotient and
  cancer risk, and which stack gives each), the count of stacks evaluated and facility-level
  warnings. A stack that cannot be evaluated gives a null per-stack result with its warning, as
  today, and does not stop the others.
- The NEI stack tool and the exposure tool descriptions say: pass ALL candidates in one
  exposure call and report the range it returns. The system prompt keeps the generic rule
  (several candidates are each evaluated and reported as a range) and loses the per-call
  checklist wording that the batch call makes unnecessary.
- The evaluation check "one exposure calculation per NEI candidate" becomes "one exposure call
  per assessed facility carrying every NEI candidate with the facility's emission rate"; the
  full-assessment scenario requirement changes accordingly.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `exposure-metrics-tool`: the tool evaluates a list of stacks per call and returns per-stack
  results plus the range; the description requirement changes from one-call-per-candidate to
  all-candidates-in-one-call.
- `stack-parameters-nei`: the description requirement says the candidates are passed together
  to one exposure calculation.
- `agent-evaluation`: the count check and the full-assessment scenario expect one exposure call
  per facility carrying every candidate.

## Impact

- `tools/exposure/metrics.py` (signature, description), `tools/schemas.py` (new
  `FacilityExposure`, `ExposureRange`), `tools/exposure/helpers/assessment.py` (loop and range;
  per-stack assessment unchanged), `tools/emissions/stack.py` (description),
  `prompts/agent_system.md`, `evals/checks.py`, `evals/scenarios.py`, their tests and the
  description-audit phrases, README tool-flow sentence.
- Callers that passed `stack_params` must pass `stacks=[...]`. The only caller is the agent.
- Recorded cassettes are unaffected: the exposure tool runs live during replay.
- Prerequisite: `add-agent-evaluation` is archived first, so its `agent-evaluation` spec exists
  in the main specs for this delta to modify.
