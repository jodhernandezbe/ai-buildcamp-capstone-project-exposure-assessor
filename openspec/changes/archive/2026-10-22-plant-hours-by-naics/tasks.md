## 1. Configuration

- [x] 1.1 Add the `[plant_hours]` section to `config/settings.toml` (baseline_path, code_column, hours_column, min_digits, max_digits, days_per_year, max_hours_per_week) with comments
- [x] 1.2 Add `config/plant_hours.py` (`PlantHoursSettings`, loader, cached getter, validators naming the key) and `tests/config/test_plant_hours_settings.py` covering the defaults and each invalid value (min_digits < 1 or > max_digits, non-positive/NaN/bool days_per_year, missing keys)

## 2. Generic matcher

- [x] 2.1 Add `commons/prefix.py` `longest_prefix(table, key, *, min_length)` (pure, generic, typed) and `tests/commons/test_prefix.py`: exact, shorter prefix, specific beats general, never matches a longer table key, below-minimum prefixes ignored, empty key, minimum longer than the key, and a probe-count check

## 3. Baseline loading and resolver

- [x] 3.1 Add `tools/emissions/helpers/inventory/plant_hours.py`: `Baseline`, `load_baseline` (two columns only, row validation, duplicate drop, release from metadata, file/column/metadata problems -> empty baseline + one warning, cached read), `OperatingHours`, and `PlantHours` (normalize code, longest prefix, h/week -> h/year with 365/7, bounds check, source strings, default fallback)
- [x] 3.2 Add `tests/tools/emissions/helpers/inventory/test_plant_hours.py` with small parquet files built in tmp (synthetic placeholder values): every spec scenario of `plant-operating-hours`, including 168 -> 8760, 84 -> 4380, bad rows (0, 169, NaN, bool, null, non-digit code, duplicate), missing file, missing column, missing release metadata, no code, 1-digit and 7-digit codes, one read for many lookups

## 4. Wiring into the inventory

- [x] 4.1 Change `Reducer.records` / `_record` / `_reported` to take an optional `hours_for` resolver and use it per slot; default behavior and source "default" when it is None; update `rate.py` docstring
- [x] 4.2 Forward `hours_for` through `lookup_emissions` and build `PlantHours` from the settings at the edge in `tools/emissions/inventory.py`, adding the baseline warning to the inventory warnings
- [x] 4.3 Add `operating_hours_source` to `EmissionRecord`, update the `fetch_emissions` docstring, and extend the reducer/lookup/inventory tests: two facilities with different hours in one lookup, matched vs default, rate = annual release / (hours x 3600), unchanged results when no resolver is given
- [x] 4.4 Carry the field through `api/schemas/workspace.py` and the projectors, re-run `scripts/export_contract.py`, and run `npm --prefix frontend ci && npm --prefix frontend run check`; update API tests

## 5. Evals and prompt

- [x] 5.1 Read the provenance check in `evals/` and decide whether the report must name the operating-hours source. Decided: no prompt rule or check. The batch assessment's facility rows do not show the model the hours (only the workspace carries `operating_hours_source`), so requiring the report to name it would test something the model is never told; the existing Limitations rule already covers a default input.
- [ ] 5.2 Run `uv run pytest -m eval` (needs the OpenAI key, costs tokens; ask before running), 3 times as the memory suggests; re-record the full-assessment cassette only if replay no longer matches, and tell the user which numbers moved

## 6. Verification

- [x] 6.1 Spot-check against the real baseline: a facility whose code has a 4-digit row (hours = h/week x 365/7), one without (default 8,760), and print the source strings
- [x] 6.2 Run `uv run pytest`, `uv run ruff format .`, `uv run ruff check .`, `uv run pyright`, bandit, the function-length check and `uv run pre-commit run --all-files`
