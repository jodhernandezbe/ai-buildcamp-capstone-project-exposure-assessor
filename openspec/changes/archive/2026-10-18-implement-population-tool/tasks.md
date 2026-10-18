## 0. Checks before coding

- [x] 0.1 Get a free Census API key, add `CENSUS_API_KEY` to `.env`, and confirm the draft's ACS request works with `key=...` (a 200 with the header row and tract rows); record the response's null and negative codes seen
- [x] 0.2 Check the screening default: compare the age mix (5.7, 16.0, 60.9, 17.4) with the national ACS DP05 row for the configured vintage, and find or drop a source for 300 residents per km2; cite in `settings.toml`
- [x] 0.3 Check the TIGERweb service: `maxRecordCount` and the `exceededTransferLimit` field, that `distance` works with a point and meters, and that the current-vintage layer id is stable (layer 8); note findings in the settings comments

## 1. Configuration

- [x] 1.1 Add `[population]` (URLs, layer, fields, vintage, variables, key variable name, radii, county cap, request policy, screening default) to `config/settings.toml`; add `CENSUS_API_KEY` to `.env.example`
- [x] 1.2 `config/population.py`: `PopulationSettings`, loader and cached getter with validation per the app-configuration delta; tests with a negative case per key

## 2. Model

- [x] 2.1 `models/population.py`: `scale_to_circle` and `age_bands` per the model spec; tests for every scenario plus rounding, large counts and each non-nested case

## 3. Transport

- [x] 3.1 `tools/http.py`: `HttpRequestError.status_code` (None when there was no answer); existing tests unchanged, new tests for the attribute

## 4. Census helper

- [x] 4.1 `tools/exposure/helpers/census.py`: tract query (truncation check, field checks, grouping by state and county) and per-county ACS query (key parameter, header-based columns, sentinel handling, redirect/401/403 = key problem); tests with synthetic payloads (round numbers, fake codes), including a 302 to a missing-key page, null and negative cells, a missing column, a truncated tract list and a county with no rows

## 5. Tool

- [x] 5.1 `tools/exposure/helpers/receptors.py`: validation, key check, county cap, counts -> model -> result, screening default with a reason for every failure; no key value in any warning; tests for every scenario of the tool spec
- [x] 5.2 Replace `tools/exposure/population.py` with the thin tool (client and key read at the edge); extend `Population` in `tools/schemas.py` (`source`, `warnings`) and remove the local type
- [x] 5.3 Re-register the tool in `tools/exposure/__init__.py`; update `tests/tools/exposure/test_metrics.py` (no population import) and add `tests/tools/exposure/test_population.py` (schema, description, end to end with a mock transport, invalid input without a request, no key without a request)
- [x] 5.4 Smoke test skipped without `CENSUS_API_KEY` (a `census` marker like `comptox`): real tracts and counts, plausible totals and age bands, a future vintage or open-water point returns the labelled default
- [x] 5.5 README: tool implemented, the key, data sources, method limits, the default

## 6. Gates

- [x] 6.1 `uv run ruff format .`, `ruff check .`, `pyright`, `bandit`, the function-length check, `pytest` and `pre-commit run --all-files` all pass
- [x] 6.2 `openspec validate implement-population-tool --strict` passes
