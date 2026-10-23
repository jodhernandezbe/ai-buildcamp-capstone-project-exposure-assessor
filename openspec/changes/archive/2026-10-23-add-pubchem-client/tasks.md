## 1. Configuration

- [x] 1.1 Add `[pubchem]` to `config/settings.toml`: URL templates (`cid_by_smiles`, `cid_by_name`, `pug_view`), `user_agent`, `delay_seconds = 0.25`, `timeout_seconds`, `max_retries`, `backoff_seconds`, `agreement_ratio`, `[pubchem.cache]` (`enabled`, `path`, `ttl_days`), `cas_heading`, and `[[pubchem.fields]]` for molecular_weight, vapor_pressure and density (key, heading path, target_unit, optional temperature range and `allow_missing_temperature`); no toxicity fields
- [x] 1.2 Add PubChem unit spellings to `[units.aliases]` (for example `g/cu cm`, `mm Hg`) after checking real PUG View spellings
- [x] 1.3 Add `config/pubchem.py` (frozen `PubchemSettings`, field specs, loader) and export it from `config/loader.py`; reject a delay below 0.2 s, templates without their placeholder, non-positive or non-finite numbers, and a field whose target unit differs from the CompTox one for the same key
- [x] 1.4 Tests in `tests/config/test_pubchem_settings.py`: shipped values and a negative test per rule

## 2. Identifiers and RDKit

- [x] 2.1 `identifiers.py`: kind detection (CAS, SMILES, name; explicit override), RDKit canonicalization with logging blocked, `ValueError` for malformed or empty input, URL encoding
- [x] 2.2 Tests: valid CAS and bad check digit, `CCCC` and an equivalent spelling canonicalize alike, `C(C` raises, `n-hexane` is a name, `kind` override, characters needing encoding, empty input

## 3. Request policy and cache

- [x] 3.1 `cache.py`: SQLite response cache with injected clock, TTL, success and 404 entries, no failures cached, fail-soft with a warning on `sqlite3.Error`/`OSError`
- [x] 3.2 `client.py` transport: `CachedJsonClient` over `RetryingClient`; `build_client(settings)` at the outer edge with the User-Agent header
- [x] 3.3 Tests with `httpx.MockTransport` and fake clock/sleep: delay before each request, 429 then success, repeated failure, 404 not retried, cache hit, cached not-found, failure not cached, expiry, corrupt file, unwritable directory, disabled cache

## 4. CID discovery, record and CAS confirmation

- [x] 4.1 `get_cid_by_identifier` (SMILES and CAS/name endpoints), single/none/many/malformed handling, reason on every `None` (`Lookup` dataclass)
- [x] 4.2 `fetch_pubchem_pug_view_json` with `Record` check and CID validation
- [x] 4.3 `sections.py` heading traversal and CAS confirmation of a record
- [x] 4.4 `resolve_compound_data` composing kind, CID, record and confirmation, returning warnings
- [x] 4.5 Tests: butane SMILES and CAS `106-97-8`, hexane CAS `110-54-3`, 404, several CIDs, non-list, bool and negative CIDs, unreachable, invalid CID raises, record with the CAS, with another CAS only, with none, SMILES/name not needing confirmation

## 5. Property extraction

- [x] 5.1 `statements.py`: structured and text statements, single number and unit, rejection of ranges/inequalities/estimates/several numbers, temperature window
- [x] 5.2 Agreement rule (median within `agreement_ratio`, else conflict reason) and the field-driven extractor returning per field a reported value `(value, unit)` or a reason
- [x] 5.3 Tests on placeholder-valued fixtures of the real PUG View shape: each field, structured vs text, range, `>`, dimensionless density, wrong temperature, conflict, agreement, one statement, wrong types, empty or non-dict record, a new configured field

## 6. Wire into `fetch_chemical_properties`

- [x] 6.1 `PubchemLookup` facade (`lookup.py`) that resolves a CAS, confirms it, extracts the requested fields and never raises on data problems
- [x] 6.2 In `properties.py`: `complete_from_pubchem` step after CompTox; compute the still-missing configured fields, skip PubChem if none; reuse `_add_one` so conversion and the plausibility guard apply; set `sources[field] = "PubChem"` and add the fallback warning; keep CompTox warnings; never touch the name or toxicity; keep the key check before any PubChem request
- [x] 6.3 Add the optional collaborator to `lookup_chemical_properties` (None = no fallback) and build the default in `_services()`
- [x] 6.4 Update the `ChemicalProperties` comments in `tools/schemas.py`; leave the tool description unchanged (a PubChem wording made the full-assessment eval unstable, see design)
- [x] 6.5 Tests in `tests/tools/informatics/`: no call when nothing missing, one gap filled, CompTox value never overwritten, rejected CompTox value retried, unit conversion from PubChem spelling, incompatible unit, PubChem down, unconfirmed match, CAS unknown to CompTox but confirmed by PubChem (name None), key unset raises before PubChem, caller mutation does not alter later results

## 7. Verification

- [x] 7.1 Add `tests/smoke/test_pubchem_fallback_live.py` (butane, CID 7843; excluded from the default run)
- [x] 7.2 Confirm `.cache/` is ignored and no test writes outside a temp directory
- [x] 7.3 Run `uv run ruff format .`, `ruff check .`, `pyright`, `bandit`, the function-length check (max 18), `uv run pytest`, `npm --prefix frontend run check`; fix to zero errors without `# noqa` or raising limits
- [x] 7.4 Run `uv run pytest -m eval` three times with the final code and compare with earlier runs
- [x] 7.5 `uv run pre-commit run --all-files`; update the `fetch_chemical_properties` paragraph in `README.md`
