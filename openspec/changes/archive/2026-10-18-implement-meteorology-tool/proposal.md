## Why

`get_meteorological_boundary` supplies the wind and stability inputs of the dispersion model, and it exists only as a working draft: it reads one year of hourly Open-Meteo data and summarizes it, but it does not follow the project's rules. It hard-codes the URL, request parameters, timeout and fallback values; two functions are 33 and 56 lines (limit 18); a pure rule (Pasquill-Gifford classification) lives in a tool; it redefines the shared `Meteorology` type with different fields; it catches every exception and silently returns made-up conditions; it validates no input; and it has no tests (the old stub tests now fail, and one of them makes a live request). This change moves the draft into the project's layers without changing its method, and makes its failures visible.

## What Changes

- Keep the draft's method: one reporting year of hourly data -> annual mean wind speed (not below a configured minimum), prevailing wind direction (modal 10 degree sector, direction the wind blows from), modal Pasquill-Gifford class and annual mean ambient temperature (for plume rise).
- Move the pure parts to `models/`: the Pasquill-Gifford classification (table-driven instead of nested conditions) and the summary of the hourly series (units in every docstring, `ValueError` on invalid input, no I/O).
- Move the I/O to a helper that fetches and validates the hourly series from Open-Meteo through an injected HTTP client, with a throttled, retrying request. The retry/backoff core is shared with the Envirofacts client instead of copied (see design D4).
- Move every URL, request parameter, timeout, retry value, year range, minimum wind speed, sector width and fallback value to a `[meteorology]` table in `settings.toml` with a typed loader.
- Validate the inputs (latitude -90 to 90, longitude -180 to 180, finite, not boolean; year an integer in the available range) before any request.
- Replace the silent fallback: when data are unavailable the tool returns the configured screening default, labelled as such with a warning that says why. It never raises on data or network problems and never hides them.
- Extend the shared `Meteorology` type (in `tools/schemas.py`) with `ambient_temperature` (K), `source` and `warnings`, replacing the draft's local type, `ambient_temperature_k` and `resolution_method`; update `calculate_exposure_metrics` documentation accordingly.
- Replace the stub tests with tests using synthetic hourly payloads (round numbers, no network); add a live smoke test.

## Capabilities

### New Capabilities
- `meteorological-conditions-tool`: the tool: representative conditions at a point for a year, input validation, provenance, screening default on failure.
- `atmospheric-stability-model`: the pure Pasquill-Gifford classification and the summary of an hourly series.

### Modified Capabilities
- `app-configuration`: new `[meteorology]` settings with validation.

## Impact

- Code: `tools/exposure/meteorology.py` (thin tool), new `tools/exposure/helpers/openmeteo.py`, new `models/stability.py` and `models/meteorology.py`, `config/meteorology.py`, `config/settings.toml`, `tools/schemas.py`, a shared retrying JSON transport at `tools/` root used by `tools/emissions/helpers/efservice.py` (behavior unchanged), `tools/exposure/metrics.py` docstring, README.
- Tests: `tests/models/`, `tests/tools/exposure/`, `tests/config/`, `tests/smoke/`; the existing stub tests are replaced.
- Dependencies: none new (httpx and numpy are already used).
- External service: Open-Meteo historical archive, no API key. Its terms (non-commercial free tier, attribution) must be checked before any production use (design risks).
