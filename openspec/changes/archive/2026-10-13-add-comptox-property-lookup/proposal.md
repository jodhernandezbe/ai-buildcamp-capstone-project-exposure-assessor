## Why

The `fetch_chemical_properties` tool is still a stub, and the SMILES lookup now gives us a structure identifier but nothing consumes it. EPA's CompTox Chemicals Dashboard API offers experimental and predicted physical-chemical properties keyed by DTXSID, so we can supply vapor pressure and density for the dispersion and risk steps.

## What Changes

- Add a CompTox helper that resolves a canonical SMILES to a DTXSID, then fetches the property summary for that DTXSID.
- For each requested property, pick `experimentalMedian`; fall back to `predictedMedian` only when no experimental value exists. Return the value, its `unit` and which source it came from.
- Drive property extraction from a configured list of properties (CompTox `propName` -> our key), initially "Vapor Pressure" and "Density". Adding a property means adding a config entry, not changing code.
- Add a `[comptox]` section to `config/settings.toml` (base URL, DTXSID-by-SMILES path, property-by-DTXSID path, API-key header name, API-key environment variable name, timeout, delay, property list) and extend the typed loader.
- Read the API key from the environment (`.env`), never from code or config.

## Capabilities

### New Capabilities
- `comptox-property-lookup`: resolve SMILES to DTXSID via CompTox and extract configured chemical properties (experimental preferred over predicted) with units.

### Modified Capabilities
- `app-configuration`: settings now also cover CompTox (endpoints, header and env-var names, timing, extractable property list), and the loader returns settings for more than one service.

## Impact

- New: `tools/informatics/helpers/comptox.py` (exported from `helpers/__init__.py`), tests under `tests/tools/informatics/helpers/`.
- Changed: `config/settings.toml`, `config/loader.py` (and `tests/config`), `tools/schemas.py` (new typed payload for a looked-up property), `.env.example` (new key name).
- No new dependencies (`httpx` already present). `fetch_chemical_properties` stays a stub; wiring it to this helper (plus molecular weight, RfC, IUR) is a later change.
- `tools/informatics/example.txt` contains a literal API key. It is untracked; it must not be committed.
