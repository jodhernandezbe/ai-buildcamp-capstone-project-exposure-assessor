## Context

`config/` holds a typed loader that today returns only `PubChemSettings`; `tools/informatics/helpers/smiles.py` shows the established helper pattern (injectable `httpx.Client` and `sleep`, per-input cache, errors logged and mapped to `None`). `fetch_chemical_properties` in `properties.py` is a stub returning molecular weight, vapor pressure, RfC and IUR. See `tools/informatics/example.txt` for the two CompTox calls: `chemical/detail/search/by-smiles/` (returns a list with `dtxsid`) and `chemical/property/summary/search/by-dtxsid/{dtxsid}` (returns a list of entries with `propName`, `unit`, `experimentalMedian`, `predictedMedian`).

## Goals / Non-Goals

**Goals:**
- A `ComptoxLookup` helper mirroring `SmilesLookup`: SMILES -> DTXSID -> `{key: PropertyValue}`.
- Property selection entirely config-driven.

**Non-Goals:**
- Wiring `fetch_chemical_properties` to the helper, or sourcing molecular weight, RfC and IUR.
- Unit conversion (e.g. mmHg to Pa, g/cm^3 to kg/m^3); callers convert.
- Batch/async lookups.

## Decisions

1. **Location: `tools/informatics/helpers/comptox.py`**, exported from `helpers/__init__.py`. Matches `smiles.py` and keeps `properties.py` as the `@tool` layer. Alternative: put the helper directly in `properties.py` as the request literally says; rejected because tool rules say that file is tool logic and the helper pattern already exists. Easy to move if preferred.
2. **Config shape.** New `[comptox]` table: `base_url`, `dtxsid_by_smiles_path` (with `{smiles}`), `properties_by_dtxsid_path` (with `{dtxsid}`), `api_key_header`, `api_key_env_var`, `delay_seconds`, `timeout_seconds`; and a list of `[[comptox.properties]]` tables with `key` and `name` (e.g. `key = "vapor_pressure"`, `name = "Vapor Pressure"`). An array of tables leaves room for per-property options later. Alternative: a flat `name -> key` map; rejected as harder to extend. <!-- pragma: allowlist secret -->
3. **Loader.** Add `ComptoxSettings` and `PropertySpec` frozen dataclasses and `load_comptox_settings` / `get_comptox_settings`; keep `load_settings`/`get_settings` returning `PubChemSettings` so existing callers and tests are untouched. Reuse the existing validators, generalised with a section-name parameter so error messages name the right key.
4. **Experimental-first selection.** Per summary entry: `experimentalMedian` if not null, else `predictedMedian` if not null, else skip. Result type `PropertyValue` (TypedDict in `tools/schemas.py`): `value: float`, `unit: str`, `source: Literal["experimental", "predicted"]`.
5. **Matching by `propName`**, exact and case-sensitive, since the names are CompTox's own identifiers. If a name appears twice, the first entry wins.
6. **DTXSID selection.** Use the first element of the by-SMILES list. A SMILES search is structure-exact, so multiple hits are not expected; log at debug if more than one.
7. **API key.** Read from the env var named in config at request time (so `.env` loaded by the app is honoured and tests can use `monkeypatch`). Missing key raises `RuntimeError` naming the variable; this is a setup error, not a service failure, so it is not swallowed. `.env.example` gets the variable name with an empty value. The key in `example.txt` is not used anywhere.
8. **Failure handling and caching** follow `SmilesLookup`: network errors, non-200 and malformed bodies yield an empty result and are not cached; 404/empty list is a definitive miss and is cached. Cache key is the SMILES string; the cached value is the full property dict for the current config.
9. **URL building.** SMILES is URL-quoted with `safe=""` before substitution into the path template (it contains `(`, `=`, `#`, `/`, `\`, `@`).

## Risks / Trade-offs

- [Experimental median of few/conflicting measurements can be far from truth] -> Report `source` so callers can see; counts are not surfaced now.
- [CompTox API key is a shared secret in the example file] -> Not copied anywhere; `example.txt` stays untracked and the key should be rotated/removed from the file before any commit.
- [CompTox rate limits are undocumented here] -> Reuse a configurable `delay_seconds` before each request; two requests per uncached chemical.
- [Unit strings differ per property and may change] -> Passed through verbatim; downstream code must check units before using values.
- [Exact `propName` match breaks if CompTox renames a property] -> Name lives in config, so fixing is a config edit.
