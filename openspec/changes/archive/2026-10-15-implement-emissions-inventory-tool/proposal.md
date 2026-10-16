## Why

`query_emissions_inventory` is still a stub, so the agent cannot discover which facilities emit a chemical or where they are. This is the first step of the source-to-receptor chain (emissions -> stack parameters -> dispersion), and the EPA Toxics Release Inventory (TRI) via Envirofacts is the data source.

## What Changes

- Implement `query_emissions_inventory` against the Envirofacts `tri_reporting_form / tri_chem_info / tri_facility / tri_release_qty` joined view, queried by CAS number.
- **BREAKING**: drop the `reporting_year` argument. The tool takes only `cas_number`; for each facility it returns the most recent reporting year available.
- Keep only configured environmental media (for now `AIR STACK`), and keep one record per (environmental medium, facility FRS ID): the one with the latest reporting year.
- Return, per facility: FRS ID, facility name, location (latitude, longitude, address, city, county, state, ZIP), environmental medium, reporting year, `total_release` and its unit as reported.
- **BREAKING**: replace `EmissionRecord` with a richer record. It carries `total_release` + `unit` as reported (TRI reports pounds per year) and also `emission_rate` in g/s and the `operating_hours_per_year` used to get it.
- Convert the annual release to a rate with the existing Pint-based `commons/units.py` (pounds -> grams) and a conservative 8,760 operating hours per year (continuous operation). The hours come from `config/settings.toml` (`[emissions] operating_hours_per_year`) through one dedicated helper, so it can later grow into something more robust (facility- or sector-specific hours) without changing callers.
- Fetch from Envirofacts in sequential, configurable-size pages with a delay between requests, retry with backoff on throttling/transient errors, and a page cap. Rows are reduced to the kept records while streaming, so memory does not grow with the raw row count.
- Add a `[tri]` section to `config/settings.toml` (base URL, path template, page size, delay, timeout, retries, page cap, media to keep) and an `[emissions]` section (operating hours per year), both with typed loaders; add a `Pounds` entry to `[units.aliases]`.

## Capabilities

### New Capabilities
- `emissions-inventory-tool`: look up facilities reporting releases of a chemical to configured media, deduplicated to the latest year per facility and medium, with location and reported quantity and unit.

### Modified Capabilities
- `app-configuration`: add requirement for externalized, validated TRI/Envirofacts settings (new requirement; existing ones unchanged).

## Impact

- Code: `tools/emissions/inventory.py` (tool), new `tools/emissions/helpers/` modules (fetch, reduce, rate), `tools/schemas.py` (`EmissionRecord`), `config/loader.py` and `config/settings.toml`.
- Tests: `tests/tools/emissions/`, `tests/config/`; registry test updated for the new signature; a live smoke test next to the existing one.
- Dependencies: none new (reuse the HTTP client already used for CompTox).
- Docs/prompts: the tool docstring (what the LLM sees) and any prompt text mentioning `reporting_year` or `emission_rate`.
