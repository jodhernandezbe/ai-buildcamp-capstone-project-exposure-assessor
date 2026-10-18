## Why

`get_population_receptors` supplies the receptor population of the exposure calculation and exists only as a working draft (`tools/exposure/population.py`, uncommitted). Checking it against the live services showed it cannot work as written: the Census Data API now answers every request without an API key with a redirect to a "Missing Key" page, so the draft's ACS call always fails and its blanket `except Exception` silently returns invented numbers (300 people per km2 and a national age mix) labelled only by a provenance string. It also breaks the project's rules: hard-coded URLs, year, layer and variable codes; a 100-line function (limit 18); a local `Population` type that shadows the shared one; no input validation; no throttling or retries; and no tests. This change moves the draft into the project's layers, makes it work with a key, and makes every failure visible.

## What Changes

- Keep the draft's method: tracts that intersect a circle around the point (Census TIGERweb) -> ACS 5-year profile counts (total population, under 5, under 18, 65 and over) -> counts scaled by circle area over tract land area -> estimated residents and age bands (0-4, 5-17, 18-64, 65+) as percent of the total.
- Use the Census API key the service now requires: read from an environment variable named in `settings.toml` (the same convention as the CompTox and OpenAI keys; a free key from the Census Bureau; documented in `.env.example`). A missing or rejected key is reported as such, never mistaken for "no data".
- Move the pure parts to `models/`: the areal scaling and the age-band arithmetic (units in every docstring, `ValueError` on impossible input, no I/O).
- Move the I/O to a helper over the shared throttled, retrying client (`tools/http.py`): the tract query, one ACS query per county, shape checks, and handling of the ACS sentinel values (null or negative estimates mean "not available", and the draft's silent `max(0, ...)` is removed).
- Move every URL, layer, vintage, variable code, default radius, radius limits, request policy and the screening default to a `[population]` table in `settings.toml` with a typed loader.
- Validate the inputs (latitude, longitude, radius) before any request, and cap the radius so one call cannot trigger hundreds of county requests.
- Replace the silent fallback: when the data cannot be used the tool returns the configured screening default, labelled `source: "screening default"` with a warning saying why. It never raises on data or network problems.
- Replace the draft's local `Population` type with the shared one in `tools/schemas.py`, extended with `source` (replacing `resolution_method`) and `warnings`; re-register the tool in the exposure package and move its tests.
- Tests with synthetic tract and ACS payloads (no network, no key); a live smoke test that is skipped without a key.

## Capabilities

### New Capabilities
- `population-receptors-tool`: the tool: residents and age mix around a point, input validation, key handling, provenance, screening default on failure.
- `population-estimation-model`: the pure areal scaling and age-band arithmetic.

### Modified Capabilities
- `app-configuration`: new `[population]` settings with validation, including the name of the API key variable.

## Impact

- Code: `tools/exposure/population.py` (thin tool), new `tools/exposure/helpers/census.py` and `tools/exposure/helpers/receptors.py`, new `models/population.py`, `config/population.py`, `config/settings.toml`, `tools/schemas.py`, `tools/http.py` (the error carries the HTTP status), `tools/exposure/__init__.py`, `tools/exposure/metrics.py` (the draft already removed the tool from it), `.env.example`, README.
- Tests: `tests/models/`, `tests/tools/exposure/`, `tests/config/`, `tests/smoke/` (key-gated); `tests/tools/exposure/test_metrics.py` loses its population import.
- Dependencies: none new.
- External services: Census TIGERweb (no key) and the Census Data API (a free key is required: requests without one are redirected to a "Missing Key" page). The user must request a key from the Census Bureau.
