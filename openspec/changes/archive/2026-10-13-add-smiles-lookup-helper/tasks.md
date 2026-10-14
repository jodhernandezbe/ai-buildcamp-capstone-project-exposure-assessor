## 1. Dependencies and project docs

- [x] 1.1 Add `rdkit` and `httpx` to `pyproject.toml` and run `uv sync`; confirm `import rdkit` works
- [x] 1.2 Update `CLAUDE.md` layout/dependency-direction sections to describe the `config/` package

## 2. Configuration package

- [x] 2.1 Create `config/__init__.py`, `config/settings.toml` (PubChem `base_url`, `compound_property_path`, `delay_seconds`, `timeout_seconds`) and `config/loader.py` with frozen dataclass `PubChemSettings`, `load_settings(path)` and cached `get_settings()`
- [x] 2.2 Validate keys/types/ranges (`ValueError` naming the key; `FileNotFoundError` for a missing file)
- [x] 2.3 Add `tests/config/` (with `__init__.py`) covering default load, explicit path, missing key, negative delay, missing file

## 3. SMILES lookup helper

- [x] 3.1 Create `tools/informatics/helpers/__init__.py` and `smiles.py` with `SmilesLookup` (injectable settings, `httpx.Client`, sleep), CAS normalization, RDKit canonicalization with raw fallback, and caching
- [x] 3.2 Implement PubChem fetch with SMILES-field fallback (`CanonicalSMILES`, `ConnectivitySMILES`, `SMILES`), delay before request, and non-raising error handling with debug logs
- [x] 3.3 Add `tests/tools/informatics/helpers/` (with `__init__.py`) using `httpx.MockTransport`: success, unknown CAS (404), blank input, field fallback, RDKit-unparseable fallback, network error not cached, cache hit across formatting variants, delay honored

## 4. Verification

- [x] 4.1 Run `uv run ruff format .`, `ruff check .`, `pyright`, bandit command, and `pytest`; fix findings
- [x] 4.2 Run `uv run pre-commit run --all-files` and confirm `.secrets.baseline` needs no changes
