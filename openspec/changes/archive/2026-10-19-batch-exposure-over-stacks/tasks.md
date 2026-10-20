## 1. Prerequisite

- [x] 1.1 Archive `add-agent-evaluation` (complete) so the `agent-evaluation` spec is in the main specs

## 2. Schema and assessment

- [x] 2.1 `tools/schemas.py`: `StackExposure` (today's `ExposureMetrics` fields plus `stack_number` and the four stack values), `ExposureRange`, `FacilityExposure`
- [x] 2.2 `assess_facility` in `tools/exposure/helpers/facility.py`: list validation, per-stack loop over the unchanged `assess_exposure`, range with the stack behind each end, counts and facility warnings; tests for every spec scenario (several stacks equal to single evaluations, one bad stack, empty list, null IUR range, doubled emission)

## 3. Tool and descriptions

- [x] 3.1 `calculate_exposure_metrics` takes `stacks: list[StackParameters]` and returns `FacilityExposure`; description rewritten (all candidates in one call, report the `range`); tool tests updated
- [x] 3.2 NEI tool description: pass ALL candidates together; audit phrases in `tests/tools/test_tool_descriptions.py` for both tools
- [x] 3.3 Prompt: drop the checklist/count sentences, keep the batching and "say if any is left out" rules; prompt tests
- [x] 3.4 README tool-flow sentence

## 4. Evaluation

- [x] 4.1 `evals/checks.py`: `exposure_covers_every_candidate` replaces `one_exposure_per_candidate`; unit tests (subset, extra call, wrong rate, pass)
- [x] 4.2 `evals/scenarios.py` uses the new check; run `uv run python -m evals run` three times and record the outcome in this file
  - Outcome (2026-10-19, `gpt-4.1`): every deterministic check passed 3/3, including one exposure call per facility carrying all 10 candidates (before: 5-6 of 10 in every failing run); `chemical-name-only` 3/3. The report judge failed 1/3 (weather source not named): report-wording variance, not fan-out.
  - Found on the way: with only the worst case ranged, reports dropped the representative case; `range.representative` added (spec and design updated). The prompt now also forbids suggesting a remembered CAS.

## 5. Gates

- [x] 5.1 ruff, pyright, bandit, function length, pytest, pre-commit all pass
- [x] 5.2 `openspec validate batch-exposure-over-stacks --strict` passes
