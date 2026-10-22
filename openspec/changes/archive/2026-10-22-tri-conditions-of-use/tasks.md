## 1. Configuration

- [x] 1.1 Add `/tri_chem_activity` after `tri_submission_naics` in `[tri].release_path`, and the `[conditions_of_use]` section (crosswalk_path, level, column names, section_pattern, `[conditions_of_use.flags]` for the 15 Section 3 flags) to `config/settings.toml`, with comments
- [x] 1.2 Add `config/conditions_of_use.py` (typed settings, loader, cached getter, validators naming the key) and `tests/config/test_conditions_of_use_settings.py`; update the TRI settings test for the new path

## 2. Crosswalk mapping

- [x] 2.1 Commit-ready `data/tsca_cou_cdr_tri_crosswalk.csv` (already present); add `tools/emissions/helpers/inventory/conditions.py`: crosswalk loader (once, cached, missing file/column -> unavailable with one warning), `Condition`, `Conditions`, and `ConditionsMapper` (level-1 rows without sub-use, section normalisation, ordering, dedup, stages, unmapped warning, notes)
- [x] 2.2 Tests `tests/tools/emissions/helpers/inventory/test_conditions.py`: every `tri-conditions-of-use` mapping scenario on a small synthetic crosswalk, the failure paths, and a check against the real CSV (every configured flag has a row; 3.3c maps to two conditions; 3.2e keeps "None (CDR exempt)")

## 3. Reading activities without duplicates

- [x] 3.1 In `reduce.py`: parse the flags into `Report.activities` (set only for 1 or "1"), record whether any activity column was present, fold into `Slot` (new slot, same-year union, later year replaces, earlier year ignored) and count rows without activity columns in `Stats`
- [x] 3.2 Pass an optional `conditions_for` through `Reducer.records` and `lookup_emissions`, add `conditions_of_use`, `lifecycle_stages` and `conditions_note` to `EmissionRecord`/`_reported`, and build the mapper at the edge in `tools/emissions/inventory.py`
- [x] 3.3 Tests for 3.1-3.2 in `test_reduce.py`, `test_lookup.py` and `test_inventory.py`: flag values (1, "1", 0, null, "yes", True, 2), union and replacement by year, repeated rows give one condition, same facilities and releases with and without activity columns, the request path contains the join, no activity columns -> note, all zeros -> note; update `tests/tools/emissions/records.py`
- [x] 3.4 Update the `query_emissions_inventory` docstring for the three new fields (what a condition of use is, several can apply, CDR-exempt strengths, the note) and its test

## 4. Workspace and UI

- [x] 4.1 API: `ConditionOfUse` model and the three fields (with defaults) on `Facility`; pass them through `EmissionPayload` and the projectors; tests in `tests/api`
- [x] 4.2 Run `uv run python -m scripts.export_contract` and `npm --prefix frontend run gen:types`; show the stages and conditions in `FacilityHoverCard.tsx` ("not reported" with the note when empty); Vitest test beside it; `npm --prefix frontend run check`

## 5. Verification

- [x] 5.1 Live check (needs network): run one real lookup (e.g. n-hexane or benzene), confirm the same facility count as before the join, time the request against the previous one, and print a few facilities' stages and conditions next to the Form R flags they came from
- [x] 5.2 Eval impact: run the deterministic eval harness tests; ask before the token-costing `pytest -m eval`, and re-record the cassette only if replay no longer matches
- [x] 5.3 Run `uv run pytest`, `uv run ruff format .`, `uv run ruff check .`, `uv run pyright`, bandit, the function-length check and `uv run pre-commit run --all-files`
