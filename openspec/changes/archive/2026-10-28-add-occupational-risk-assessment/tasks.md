## 1. Configuration and occupational model

- [x] 1.1 Add `[occupational]` to `config/settings.toml` (two ventilation tiers in ft^3/min and mixing factor, 10 and 20 m^3/day, 250 worker days, 40 y tenure, 78 y lifetime, tier thresholds) with a typed loader `config/occupational.py` and negative tests (non-positive rates, mixing factor above 1)
- [x] 1.2 Implement `models/exposure/occupational.py` (box model, TWA, OEL ratio, ADC/LADC, HQ, CR, tier) with units in every docstring and each function at most 18 lines
- [x] 1.3 Add `tests/models/exposure/test_occupational.py`: worked example, doubling, tier ordering, 16 h vs 4 h TWA, tenure cancelling in ADC, CR units, null RfC/IUR, tier boundaries and invalid inputs

## 2. PubChem occupational limits

- [x] 2.1 Add `[[pubchem.limits]]` (heading path, kind, programme), the TWA priority list and the 24.45 L/mol molar volume to `config/settings.toml` and `config/pubchem.py`; confirm the real PUG View headings against a live record
- [x] 2.2 Add `tools/informatics/helpers/pubchem/limits.py`: read statements with the existing record walker, ppm to mg/m^3 with the extracted molecular weight, fail-closed skips with reasons, benchmark selection OSHA then NIOSH then ACGIH
- [x] 2.3 Add the `OccupationalLimits` type to `tools/schemas.py` and return it with the chemical properties from the same cached response (no extra request)
- [x] 2.4 Tests under `tests/tools/informatics/helpers/pubchem/`: ppm conversion, mg/cu m, ranges and inequalities skipped, no molecular weight, priority order, missing section, cache hit makes no request; extend the live smoke test

## 3. Operating schedule and profile

- [x] 3.1 Add `shift_hours_per_day` to `[plant_hours]` and its loader, with negative tests (weeks per year follow the existing `days_per_year` / 7)
- [x] 3.2 Derive the schedule (days per week, hours per day, operating days, annual hours) from the facility's operating hours per year in `schedule.py`, so it always agrees with the matched hours; `OperatingHours` and the hours/source on the record are unchanged
- [x] 3.3 Ship `data/cdr_naics_industrial_sector.csv` (NAICS prefix to IS code, name, NAICS edition, source) taken from EPA's Table 5 "NAICS and IS Crosswalk" (IUR Technical Support Document, Oct 2009; NAICS 2007), with a loader (`[cdr_sector]`, `sector.py`) doing longest-prefix match and only the rows that table states (NAICS 48, 49 and 213 left out: the merged cell does not say which sector they belong to)
- [x] 3.4 Build the `OperationalProfile` (NAICS, stages and COU from the existing activities, CDR sector, schedule, sources) and add it to `tools/schemas.py`
- [x] 3.5 Tests in `tests/tools/emissions/helpers/inventory/` (the request's `tests/tools/test_operating_schedule.py` maps here): schedule derivation incl. 40 h, 80 h and 168 h, default, sector match and no match, no activities not defaulted

## 4. Inventory: fugitive release and provenance

- [x] 4.1 Add `[tri].fugitive_medium` (`AIR FUG`), read it in one more query, fold it into the stack record of the same facility as `fugitive_release_kg_per_year` and `fugitive_reporting_year` (shared unit conversion); fugitive-only facilities are not listed as stack sources
- [x] 4.2 The record's `operating_hours_per_year` is the annual operating hours (already on the record, with its source); the profile reports it as `annual_operating_hours`. The inventory cache is in memory per process, so no key change is needed
- [x] 4.3 Tests: both media, stack only, fugitive only, reported zero, unconvertible unit, other facilities not mixed up, stack numbers unchanged; update the lookup and inventory fakes

## 5. Assessment wiring

- [x] 5.1 Add the occupational step to `tools/assessment/` (fail closed per Spec: null without release, limit or toxicity values; assumptions in warnings) and call it from `chain.py` for every evaluated facility, not for screened-out ones
- [x] 5.1a Add `low_volatility_mmhg` to `[occupational]`; attach the chemical's vapor pressure and source (CompTox, then PubChem) to the occupational result and add the low-volatility warning without changing any value or tier; tests for volatile, non-volatile, PubChem fallback, missing and changed threshold
- [x] 5.2 Extend `FacilityAssessment` with `occupational_exposure` and `operational_profile`; `exposure` stays the community (ambient) result under its existing name, so no consumer breaks and nothing is duplicated
- [x] 5.3 Add one line per facility (tier, ratio) to the model's text view and update the assessment tool description and the system prompt to teach how to read it, without naming tools or a call order
- [x] 5.4 Tests: three results present, screening unchanged, worst-case-only facility, no per-facility requests; update `tests/tools/test_registry.py` if tools change

## 6. API and workspace

- [x] 6.1 Add `OccupationalExposure` and `OperationalProfile` to `api/schemas/workspace.py` and a projector that fills them under the fail-closed rules
- [x] 6.2 Regenerate the schema and `frontend/src/types`, run the contract test, and add API tests for finite-only values, null with reason and the `workspace_update` payload
- [x] 6.3 The Word report is not extended in this change (the report spec is unchanged); noted as a follow-up

## 7. Frontend

- [x] 7.1 Show the worker results with the community ones, not in a separate view: a "Worker exposure" card in the summary ribbon (highest across facilities, from a new `worker_risk` summary in the workspace)
- [x] 7.2 Add the community HQ and worker tier badge and a "Worker exposure" section to the facility inspector, and a worker-tier ring, legend entry and accessible name to the map markers
- [x] 7.3 Component tests for the ribbon card, the inspector section and badge, the map ring data and legend, null values ("not reported") and the schedule formatter

## 7b. Added during the work

- [x] 7b.1 Risk by group: an exposure pathway dropdown in each section ("Outdoor Air → Inhalation → General Population" / "Indoor Air → Inhalation → Worker"), worker quantities (hazard quotient, cancer risk, limit ratio) and the worker tier boundaries from the client settings
- [x] 7b.2 Ask for the occupational limit, molecular weight, vapor pressure and density when no source has them (new `oel_twa` quantity); an entered weight is used before the ppm limits are converted; the batch assessment looks the chemical up with the run's entered values, also when benchmarks are given
- [x] 7b.3 Show vapor pressure, density and the occupational limit on the chemical card, in the inspector and in the report

## 8. Quality gates

- [x] 8.1 Update `docs` or folder `CLAUDE.md` files only if a new layer rule is introduced; keep the root `CLAUDE.md` under 80 lines
- [x] 8.2 Run `uv run ruff format .`, `ruff check`, `pyright`, `bandit`, the function-length check, `uv run pytest` and `npm --prefix frontend run check` (includes the TypeScript build); fix every error
- [x] 8.3 Re-recorded the three cassettes with live tools (plus the extra calls of the full-assessment scenario) and ran `pytest -m eval` three times on the final prompt: 18 of 18 each time. A reworded 'ask only for what the tools report' sentence had dropped the CAS-from-memory scenario to 6 of 10 against 10 of 10 for the original, so the original sentence stays
- [x] 8.4 Run `openspec validate add-occupational-risk-assessment --strict`, then the pre-commit hooks
