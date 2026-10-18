## 0. Checks before coding

- [x] 0.1 Verify the Pasquill-Gifford class table and the radiation thresholds against a primary source (EPA/Turner key); record the citation in the `models/stability.py` docstring, and adjust the spec scenarios if a band differs
- [x] 0.2 Verify or replace the screening default (2.5 m/s, 270 degrees, class D, 293.15 K) and cite its source in `settings.toml`
- [x] 0.3 Check the Open-Meteo archive: the parameter that pins the model, the first available year, the lag behind the present, the reported units, and the terms of use; record the findings in the settings comments

## 1. Configuration

- [x] 1.1 Add `[meteorology]` (and its screening default) to `config/settings.toml` with comments
- [x] 1.2 `config/meteorology.py`: `MeteorologySettings`, loader and cached getter, validation per the app-configuration delta; tests with a negative case per key

## 2. Models

- [x] 2.1 `models/stability.py`: table-driven `classify_stability`, `ValueError` on impossible input; tests for every scenario of the spec and for every band edge and category combination
- [x] 2.2 `models/meteorology.py`: `summarize_hours` (mean wind with minimum, circular modal sector, modal class with deterministic ties, mean temperature in degrees Celsius); tests for the clamp, wrap-around, ties, empty and mismatched input

## 3. Shared transport

- [x] 3.1 `tools/http.py`: `RetryingClient.get_json(url, params)` with the throttle, retry, backoff, `Retry-After` and timeout behavior of `EfserviceClient`; tests for the generic core (params, shape-agnostic result, errors)
- [x] 3.2 Make `EfserviceClient` a thin wrapper over it; the existing `test_efservice.py`, `test_tri.py`, `test_frs.py` and `test_nei_lookup.py` pass unchanged

## 4. Open-Meteo helper

- [x] 4.1 `tools/exposure/helpers/openmeteo.py`: request from settings, response shape and unit checks, equal-length series, validity mask and excluded-hour count; tests with synthetic hourly payloads (round numbers, no network): valid year, missing values, out-of-range values, missing `is_day`, mismatched lengths, wrong units, client error not retried, throttled then success
- [x] 4.2 Confirm against the live API that the request parameters (including the model parameter, if used) are accepted

## 5. Tool

- [x] 5.1 Replace the draft in `tools/exposure/meteorology.py` with the thin tool: input validation, year window with an injected clock, helper + models, Pint conversion of the mean temperature, screening default with a reason on any data problem; write the description per the spec
- [x] 5.2 Extend `Meteorology` in `tools/schemas.py` (`ambient_temperature`, `source`, `warnings`), remove the local type, update the `calculate_exposure_metrics` docstring
- [x] 5.3 Replace `tests/tools/exposure/test_meteorology.py`: schema (arguments `latitude`, `longitude`, `reporting_year`), description content, every scenario of the tool spec, no real network
- [x] 5.4 Live smoke test (`-m smoke`): shape, plausible ranges, direction and unit checks for a known location

## 6. Docs and gates

- [x] 6.1 Update the README (tool implemented; data source, resolution, default behavior, terms)
- [x] 6.2 `uv run ruff format .`, `ruff check .`, `pyright`, `bandit`, the function-length check, `pytest` and `pre-commit run --all-files` all pass
- [x] 6.3 `openspec validate implement-meteorology-tool --strict` passes
