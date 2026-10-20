## Context

`calculate_exposure_metrics(emission_rate, stack_params, meteorology, population, toxicity)`
evaluates one stack through `assess_exposure` (`tools/exposure/helpers/assessment.py`), which
validates, runs the SCREEN3 grid and builds an `ExposureMetrics`. The NEI tool returns up to
`[stack.nei].max_candidates` (10) candidates. The evaluation harness replays network tools and
runs this tool live, and `evals/checks.py` counts one exposure call per candidate. Evidence from
`evals/reports/` (2026-10-19): `gpt-4.1` batches the per-stack calls in one turn but emits only
5–6 of 10; see proposal.

## Goals / Non-Goals

**Goals:**
- One exposure call per facility carries all its candidates; the per-stack loop runs in code.
- Per-stack results keep today's content, so nothing the report says per stack changes.
- A range the agent can report directly, with the stack behind each end.
- Smaller tool-call payload: shared inputs appear once.

**Non-Goals:**
- Changing the dispersion, dose or risk calculations.
- Evaluating several facilities in one call (the facility's weather and population differ).
- Choosing among the stacks for the agent: the range and every per-stack result are returned.

## Decisions

### D1. Extend the existing tool rather than add a second one
`calculate_exposure_metrics` keeps its name and takes `stacks: list[StackParameters]`. The old
single-stack form is removed, not kept beside it: two ways to call would let the model fall back
to one call per stack. The agent is the only caller.

### D2. Result shape: per-stack results plus a range
New `FacilityExposure` TypedDict: `results: list[StackExposure]`, `range: ExposureRange | None`,
`stacks_given: int`, `stacks_evaluated: int`, `warnings: list[str]`. `StackExposure` is today's
`ExposureMetrics` plus `stack_number` (1-based) and the four stack values echoed, so a row in
the report can be tied to its stack without the agent re-reading the candidates. `ExposureRange`
holds, for `max_concentration`, `hq` and `cancer_risk`, `{low, high, low_stack, high_stack}` or
`None` when the quantity is null for every stack, and the same three under `representative` for
the representative weather. (A first version ranged only the worst case; the eval judge then
found reports that dropped the representative case, because the summary did not offer it.)
*Alternative:* return only the range — rejected, the report needs per-stack rows and warnings.

### D3. Implementation: loop around the unchanged per-stack assessment
`assess_exposure` keeps its signature and tests; a new `assess_facility(emission_rate, stacks,
meteorology, population, toxicity, settings)` in `assessment.py` (or a sibling
`helpers/facility.py` if `assessment.py` grows past its role) validates that `stacks` is a list,
calls `assess_exposure` per stack, numbers and echoes the stack, computes the range over non-null
values with `min`/`max` keyed by value, and adds facility warnings ("3 stacks given, 2
evaluated"). Standing warnings that repeat per stack (worst case may be where nobody lives,
default weather or population) stay per stack: they are part of each result's contract.

### D4. Descriptions and prompt
NEI tool: "pass ALL candidates together to one exposure calculation; never a subset". Exposure
tool: "evaluates every stack given; pass all of a facility's candidates in one call; report the
`range`". The audit phrases in `tests/tools/test_tool_descriptions.py` change with them. The
prompt keeps "several candidates are each evaluated and reported as a range; say if any is left
out" and the one-turn batching sentence, and drops the checklist/count sentences, which the batch
call makes moot.

### D5. Evaluation check
`one_exposure_per_candidate` is replaced by `exposure_covers_every_candidate`: for each assessed
facility, exactly one exposure call whose `stacks` contain every NEI candidate (matched on the
four values, as today) and whose `emission_rate` is the facility's. The scenario's check list
and the spec change together. The existing cassette needs no re-recording.

### D6. Order of changes
`add-agent-evaluation` is archived first (it is complete) so `agent-evaluation` exists in the
main specs for this change's delta.

## Risks / Trade-offs

- [Larger single tool result (10 results in one payload)] → results are compact dicts; 10 of
  them are smaller than the 10 calls' inputs were, and the model reads rather than writes them.
- [A malformed entry in `stacks` from the model] → validated per stack as today: null result with
  a warning for that stack, the rest evaluated.
- [Agent still passes a subset] → the coverage check names the missing candidates; the
  description says "never a subset". Verified by three eval runs before closing the change.

## Migration Plan

Additive except the signature. No stored data changes. Rollback: revert the change.
