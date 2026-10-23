## 1. Assess every facility

- [x] 1.1 `tiers.screen`: no ranking cut (every candidate goes on); `max_refined` becomes a safety bound (default 5,000) whose excess is returned as `NotAssessed` with its reason and a warning; update `config/assessment.py`, `settings.toml` (comment and value) and `tests/config/test_assessment_settings.py`
- [x] 1.2 `_by_id`: refine every requested facility that is in the inventory, full chain for the first `max_facilities`, the rest worst case only; FRS IDs not in the inventory stay listed as not assessed
- [x] 1.3 Tests in `tests/tools/assessment/` for 1.1 and 1.2 (nothing dropped below the safety bound, the bound reports, by-ID beyond the cap keeps worst case only, order kept)

## 2. Carry the unassessed to the program

- [x] 2.1 Add `not_assessed` to `AssessmentArtifact` (`tools/schemas.py`) and fill it in `_artifact`; tests that the artifact lists them with their reasons
- [x] 2.2 `ScreeningOutcome` gains `not_assessed`; `api/services/projectors/assessment.py` files them as `Screening(outcome="not_assessed", reason=...)` for placed facilities only, never over a real result; projector tests (outcome and reason, no overwrite, unknown FRS ID ignored); re-export the contract and regenerate the frontend types

## 3. The card says the real reason

- [x] 3.1 `FacilityHoverCard.noStacks` and `features/overview/assessment.ts`: the three texts (screened out on the bound; not assessed with its reason; not covered by the batch yet), no "no stack parameters were obtained"; Vitest tests for each and for the outcome helper; `npm --prefix frontend run check`

## 4. Bulk same-site search

- [x] 4.1 `eis.py`: twin search by batches of names (`twins_path` with `{names}`, `twin_batch_size`), local filtering by name, state and distance, comma names individually, bisect a rejected batch, `twin_workers` batches at a time; config and its tests
- [x] 4.2 Tests with a fake FRS client: requests per batch not per facility, the same twins found as the per-facility search, comma name, rejected batch bisected, a single rejected name leaves a note and no exception

## 5. Verification

- [x] 5.1 Real run on benzene (live TRI/FRS): count facilities by outcome before and after, time the EIS lookup, confirm no facility is left without an outcome and the cards show reasons; report the numbers
- [x] 5.2 Run `uv run pytest`, `uv run ruff format .`, `uv run ruff check .`, `uv run pyright`, bandit, the function-length check and `uv run pre-commit run --all-files`; ask before the token-costing evals
