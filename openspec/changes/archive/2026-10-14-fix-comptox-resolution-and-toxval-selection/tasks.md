## 1. Configuration

- [x] 1.1 In `config/settings.toml` delete the `[pubchem]` table, replace `dtxsid_by_smiles_path` with `dtxsid_by_cas_path = "/chemical/search/equal/{casrn}"`; set toxicity `types` to RfD, RfC, "cancer slope factor", "cancer unit risk"; add `routes` and `prefer` per entry as in design; add aliases `(mg/m3)-1` and `(mg/L)-1`
- [x] 1.2 Update `config/loader.py` (remove `PubChemSettings`, `load_settings`, `get_settings` and their export in `config/__init__.py`): `dtxsid_by_cas_path`/`dtxsid_by_cas_url` with `{casrn}` check, `routes` and `prefer` on `ToxicityValueSpec` with validation
- [x] 1.3 Update and extend `tests/config/test_loader.py` (drop the PubChem tests and rebase the shared fixtures on CompTox; CAS placeholder, missing routes, bad `prefer`, defaults for the four entries)

## 2. CAS validation

- [x] 2.1 Create `tools/informatics/helpers/cas.py` with `format_cas` (hyphen normalization, check digit)
- [x] 2.2 Create `tests/tools/informatics/helpers/test_cas.py`: hyphenated, bare digits, whitespace, bad check digit, too short/long, non-digits, blank

## 3. CompTox helper

- [x] 3.1 Switch `ComptoxLookup.get_properties` / `get_toxicity_values` and the DTXSID cache to CAS input; resolve via the CAS search into a cached frozen `Chemical(dtxsid)`; verify `searchName == "CAS-RN"` and equal `casrn`; HTTP 400 "Found 0 results" is a cached no-match
- [x] 3.2 Add the route filter and per-entry conservative selection (lowest/highest within the best-ranked source) to `select_toxicity`
- [x] 3.3 Update `tests/tools/informatics/helpers/test_comptox.py` to CAS inputs and add cases for bare-number CAS, bad check digit, `Substance_id` trap, mismatched CAS, 400 zero-results vs other 400, route filter and case-insensitivity, "not specified" for RfC, wrong-route slope factor ignored, conservative selection and identical duplicates

## 4. Tool

- [x] 4.1 Update `lookup_chemical_properties`: validate CAS, call CompTox by CAS (no `SmilesLookup` argument), take molecular weight from `comptox.get_molecular_weight(cas)` with source "CompTox", warn when it is missing
- [x] 4.2 Update `tests/tools/informatics/test_properties.py` for the new flow (molecular weight missing but CompTox otherwise ok, CompTox empty, invalid CAS without key, missing key still raises for valid CAS)
- [x] 4.3 Update the `fetch_chemical_properties` docstring to state the conservative-value rule and the route used per value

## 4b. Remove the stale SMILES lookup and RDKit

- [x] 4b.1 Delete `tools/informatics/helpers/smiles.py` and `tests/tools/informatics/helpers/test_smiles.py`; update `helpers/__init__.py`, `tools/informatics/properties.py` and every import
- [x] 4b.2 Add `detail_by_dtxsid_path` (chemical detail endpoint) and a `[comptox.molecular_weight]` table (`field`, `unit`, `target_unit`) to `config/settings.toml` and the loader (`{dtxsid}` placeholder check, URL property, `MolecularWeightSpec`, tests); convert molecular weight with the unit guardrail in the tool
- [x] 4b.3 Add `ComptoxLookup.get_molecular_weight(cas)` (reads `averageMass`, finite number only, cached, shares the single CAS search); remove `Chemical.smiles` and `get_smiles`; test present, missing, non-numeric, non-finite, one CAS search
- [x] 4b.4 Delete `tools/informatics/helpers/molecule.py` and its test; remove the `rdkit` dependency (`uv remove rdkit`, refreshing `uv.lock`); confirm with a repository-wide search that no reference to `rdkit`, `SmilesLookup`, `PubChem`, `normalize_cas` or `canonicalize` remains outside archived changes

## 5. Defensive checks

- [x] 5.1 In the CompTox helper, type-check every used field, reject bool and non-finite numbers, skip ToxVal records whose `dtxsid` differs from the requested one, and return copies of cached values (including nested containers)
- [x] 5.2 Add the plausibility guard (finite and strictly positive after conversion, with a warning) to `lookup_chemical_properties`; keep `ComptoxLookup` a faithful passthrough
- [x] 5.3 Add negative tests: malformed response shapes, NaN/infinity/bool values, record for another DTXSID, zero and negative values, and a caller mutating a returned result (second call unaffected)
- [x] 5.4 Review handlers: no bare or overly broad `except`, every request carries the configured timeout

## 5b. Toxicity context for the final answer

- [x] 5b.1 Add `route`, `endpoint`, `assessment` to `ToxicityValue` and the new `ToxicityDetail` and `toxicity_details` to `tools/schemas.py`; extract them in `select_toxicity` and carry them through the cache copies
- [x] 5b.2 Add `applied_route` (first accepted route) to `ToxicityValueSpec`; build `toxicity_details` in `lookup_chemical_properties` only for values that were kept; extend the tool description
- [x] 5b.3 Tests: record context returned, unstated or non-text endpoint is None, reported vs applied route, context follows the chosen record, no entry for missing or rejected values, cached details cannot be altered; live checks for benzene (leukemia, oral/inhalation) and formaldehyde's unspecified RfC route

## 6. Smoke tests and verification

- [x] 6.1 Add smoke cases for a bare-number CAS (benzene as "71432") and an invalid CAS check digit; run `uv run pytest -m smoke` and confirm all pass
- [x] 6.2 Run `uv run ruff format .`, `ruff check .`, `pyright`, `pytest`, the bandit command and pre-commit; confirm no keys or example files are staged
