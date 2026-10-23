## 1. Subsector table

- [x] 1.1 Download Census `2-6 digit_2022_Codes.xlsx` and `2-6 digit_2017_Codes.xlsx` into `data/raw/naics/` (untracked) and add `scripts/build_naics_subsectors.py`: sheet read by header names, three-digit rows only, newest vintage wins, deterministic CSV; run it to produce `data/naics_subsectors.csv`
- [x] 1.2 Tests `tests/scripts/test_build_naics_subsectors.py` with tiny synthetic workbooks: every `naics-subsectors` table scenario (newest wins, older-only kept, other levels ignored, leading sequence column, byte-identical rerun)
- [x] 1.3 Add `subsectors_path` and the two column names to `[industry]` and `config/industry.py`; update `tests/config/test_industry_settings.py` (loaded values, invalid values naming the key)

## 2. Facility records and API

- [x] 2.1 Add `tools/emissions/helpers/naics_subsectors.py` (`subsector_titles`, `with_subsectors`) and tests: six-digit, short, missing and unlisted codes, read once, missing file/column setup errors
- [x] 2.2 Add `naics_subsector` and `naics_subsector_title` to `EmissionRecord` and the reducer's record (null), fill them in `tools/emissions/inventory.py::_titled`, document them in the `query_emissions_inventory` docstring; update `tests/tools/emissions/records.py` and the reducer/lookup/inventory tests
- [x] 2.3 Carry them through `EmissionPayload`, `Facility` and the projectors (defaults null), with API and state tests; run `uv run python -m scripts.export_contract` and `npm --prefix frontend run gen:types`

## 3. Grouping logic (frontend, pure)

- [x] 3.1 Add `frontend/src/features/overview/riskGroups.ts` (`groupFacilities`, `topGroups`, `describeBar`) and `riskGroups.test.ts` for every rule in the design (max not sum, once per facility, assessed only, no value not ranked, ties, top 5, zero values, not-reported counts)

## 4. Charts and layout

- [x] 4.1 Add `RiskGroupChart.tsx` (Recharts grouped bars, log axis, threshold reference lines, tooltip from `describeBar`, `accessibilityLayer`, hidden text table, empty-state message) with tests
- [x] 4.2 Add `RiskGroupSection.tsx` (title, ranking switch, expand/restore button, the multi-condition note) and wire three sections between the ribbon and the table in `OverviewPanel.tsx` with the shared ranking state, the expanded state (others hidden but mounted), Escape to restore, and the thresholds prop passed from `App.tsx`
- [x] 4.3 Tests: expand/restore/Escape, others stay mounted, stacked vs side-by-side, ranking switch, the panel with and without assessed facilities; `npm --prefix frontend run check` and `npm --prefix frontend run build`

## 5. Verification

- [x] 5.1 Run the app on a real assessment (`npm --prefix frontend run build`, `uv run python -m api`), screenshot the three charts, expand one, and compare a few bars with the results table values
- [x] 5.2 Run `uv run pytest`, `uv run ruff format .`, `uv run ruff check .`, `uv run pyright`, bandit, the function-length check and `uv run pre-commit run --all-files`
