## 1. API spike (no production code)

- [x] 1.1 In the scratchpad, probe Envirofacts with a few CAS numbers: record per-page latency and size for several page sizes, the maximum rows accepted per request, the response to an out-of-range page (empty list vs 404), and any 429/`Retry-After` behaviour
- [x] 1.2 Try server-side medium filters (`tri_release_qty` alone, per-year, other path forms) and decide the request path; if none works, keep client-side filtering
- [x] 1.3 Check on real rows: that `epa_registry_id` is populated whenever `frs_id` is not, duplicate rows per (medium, facility, year), `pref_longitude` sign across several states and GU/MP; update design decisions 4, 5 and 7 if reality differs
- [x] 1.4 Save a few small real-shaped rows (trimmed to needed columns, values copied from the API) as a test fixture

## 2. Configuration

- [x] 2.1 Add `[tri]` to `config/settings.toml` (base URL, path template with `{casrn}` and `{medium}` (spike: server-side filter form `.../cas_registry_number/{casrn}/environmental_medium/{medium}/rows/{start}:{end}/JSON`), page size 1000, delay, timeout 60, retries, backoff, max pages 40, filter path segment `environmental_medium/{medium}`, media = ["AIR STACK"], field names, east-longitude states), `[emissions] operating_hours_per_year = 8760`, and a `Pounds = "pound"` entry in `[units.aliases]`
- [x] 2.2 Add frozen `TriSettings` and `EmissionsSettings` with loader validation to `config/loader.py` per the app-configuration delta; add tests incl. negative cases for each invalid key (hours: missing, bool, zero, negative, > 8784, non-numeric)
- [x] 2.3 Decide CAS-validation reuse (shared in `commons/` vs copy) so tools do not import other tool folders

## 3. Schema

- [x] 3.1 Replace `EmissionRecord` in `tools/schemas.py` with the new fields (FRS ID, name, medium, year, `total_release`, `unit`, `emission_rate` g/s, `operating_hours_per_year`, latitude, longitude, address, city, county, state, ZIP) with units in comments

## 3b. Rate helper (pure)

- [x] 3b.1 Add `tools/emissions/helpers/rate.py` with `operating_hours_per_year(settings)` (returns the configured value; no numeric literal in code) and `to_emission_rate(value, unit, hours, aliases)` converting to kg with `commons.units.convert` and calling `models.risk.calculate_emission_rate` with the configured hours
- [x] 3b.2 Tests in `tests/tools/emissions/helpers/test_rate.py`: hand-checked pounds/yr to g/s value, hours taken from settings (changing the setting changes the result), unknown unit and non-mass unit raise/return absent, zero value gives zero rate, non-finite rejected

## 4. Row reduction (pure)

- [x] 4.1 Add `tools/emissions/helpers/reduce.py`: validate a row (finite non-negative number, not bool, unit present, coordinates in range, signed longitude), resolve the facility key, and fold into latest-year-per-(medium, facility)
- [x] 4.2 Tests in `tests/tools/emissions/helpers/` for: latest year wins, latest-year-null omitted (no fallback), two media per facility, other media dropped, FRS fallback, no ID skipped, bad quantity (null/negative/NaN/bool), bad coordinates, unconvertible unit discarded with warning, rate attached to kept records, western longitude sign, GU/MP

## 5. Paged fetcher

- [x] 5.1 Add `tools/emissions/helpers/tri.py`: build the page URL from settings, fetch pages sequentially with injected client and `sleep`, delay between requests, per-request timeout, retry/backoff on 429/5xx/timeouts honouring `Retry-After`, stop on short/empty page or page cap, reduce page by page
- [x] 5.2 Tests with a fake client: multi-page stop, exact offsets, 429 then success, `Retry-After`, retries exhausted gives empty plus warning, page cap warning, non-list body, non-retryable 4xx, delay and timeout passed on every call

## 6. Tool

- [x] 6.1 Implement `query_emissions_inventory(cas_number)` in `tools/emissions/inventory.py`: validate CAS, build default collaborators at the edge, return the records; rewrite the docstring (purpose, Args, Returns with units, latest-year and pounds-per-year caveats)
- [x] 6.2 Update `tests/tools/emissions/test_inventory.py` and `tests/tools/test_registry.py` for the new signature; invalid CAS makes no request
- [x] 6.3 Add a live smoke test (skipped without network) for CAS 50-00-0 next to the CompTox one
- [x] 6.4 Update any prompt text or docs mentioning `reporting_year` or `emission_rate`

## 7. Quality gates

- [x] 7.1 `uv run ruff format .`, `ruff check .`, `pyright`, `bandit`, function-length check (max 18), `pytest`, and `pre-commit run --all-files` all pass
- [x] 7.2 `openspec validate implement-emissions-inventory-tool --strict` passes (the untracked `sample.json` is the user's file and is left in place)
