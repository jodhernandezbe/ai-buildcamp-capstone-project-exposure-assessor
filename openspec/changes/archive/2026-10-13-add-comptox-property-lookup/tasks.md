## 1. Configuration

- [x] 1.1 Add `[comptox]` table and `[[comptox.properties]]` entries (vapor_pressure -> "Vapor Pressure", density -> "Density") to `config/settings.toml`
- [x] 1.2 Add `PropertySpec` and `ComptoxSettings` dataclasses and `load_comptox_settings` / `get_comptox_settings` to `config/loader.py`, with validation (non-empty strings, `{smiles}`/`{dtxsid}` placeholders, non-negative numbers, non-empty unique property list); generalise the shared validators so error messages name the right section
- [x] 1.3 Extend `tests/config/test_loader.py`: defaults load, missing section/key, bad placeholder, duplicate property key, custom path
- [x] 1.4 Add the API-key variable name (empty value) to `.env.example`

## 2. Types

- [x] 2.1 Add `PropertyValue` TypedDict (`value`, `unit`, `source`) with units documented to `tools/schemas.py`

## 3. Helper

- [x] 3.1 Create `tools/informatics/helpers/comptox.py` with `ComptoxLookup` (injectable settings, `httpx.Client`, `sleep`, env mapping): SMILES -> DTXSID -> configured properties, experimental-over-predicted selection, API-key header, caching and failure handling per design
- [x] 3.2 Export `ComptoxLookup` from `tools/informatics/helpers/__init__.py`

## 4. Tests

- [x] 4.1 Create `tests/tools/informatics/helpers/test_comptox.py` using `httpx.MockTransport` and synthetic payloads (no real-looking data): experimental preferred, predicted fallback, both null skipped, unconfigured ignored, extra configured property picked up, units passthrough
- [x] 4.2 Cover DTXSID cases: match, empty list, 404, blank SMILES makes no request, SMILES is URL-quoted
- [x] 4.3 Cover key and failure handling: header sent, missing/blank env var raises naming the variable, network error / 500 / malformed JSON return empty and are not cached, success and 404 are cached

## 5. Verification

- [x] 5.1 Run `uv run ruff format .`, `ruff check .`, `pyright`, `pytest`, and the bandit command; confirm `tools/informatics/example.txt` is not staged
