## Why

Live smoke tests (`tests/smoke/`, run with `pytest -m smoke`) show `fetch_chemical_properties` returns wrong data for real chemicals. CompTox's by-SMILES search returns an unrelated compound for aromatic (lowercase) SMILES, so benzene resolved to a furanone and toluene to a bleomycin derivative, and the tool silently reported their vapor pressure and density. Separately, the ToxVal filters do not match CompTox's real data: cancer values are labeled `cancer slope factor` / `cancer unit risk` (not `SF`, `OSF`, `IUR`), IUR is reported per mg/m3, records of the wrong exposure route are not excluded, and IRIS lists a range of slope factors and unit risks with no rule for choosing one. 13 of 28 smoke tests fail today.

## What Changes

- Resolve the DTXSID from the CAS number with CompTox's exact CAS search (`/chemical/search/equal/{casrn}`, verified live) instead of from a SMILES. Accept only a result whose `searchName` is `CAS-RN` and whose `casrn` equals the requested CAS (a bare number such as `71432` is otherwise matched as a substance ID and returns an unrelated chemical). Validate and normalize the CAS format first; HTTP 400 "found 0 results" is a definitive no-match.
- **BREAKING (internal):** `ComptoxLookup.get_properties` and `get_toxicity_values` take a CAS number, not a SMILES; the `dtxsid_by_smiles_path` setting is replaced by `dtxsid_by_cas_path`.
- Correct the toxicity filters: accepted labels become `RfD`, `RfC`, `cancer slope factor` and `cancer unit risk`; each toxicity entry also lists the exposure routes it accepts (oral for RfD and SF, inhalation for RfC and IUR; "not specified" also for RfD and RfC, whose names already imply the route), compared case-insensitively.
- Among records from the best-ranked source, choose the most conservative value, configured per entry: lowest for RfD and RfC, highest for SF and IUR.
- Report the context of every toxicity value so the final answer can explain it: the exposure route it applies to (and the route the source recorded), the source, the critical effect or cancer endpoint (e.g. leukemia), and whether it is a cancer or non-cancer value.
- Add the CompTox unit spellings seen live to the alias table (`(mg/m3)-1`, `(mg/L)-1`).
- **Remove the SMILES lookup and RDKit.** With CompTox queried by CAS, the PubChem CAS-to-SMILES step is stale, and so is calculating molecular weight from a structure: CompTox serves it directly as `averageMass` (g/mol) on its chemical detail endpoint (verified live for benzene, toluene, formaldehyde, carbon tetrachloride and water; values match RDKit's). Delete `SmilesLookup`, `normalize_cas`, `canonicalize`, the `[pubchem]` configuration and its loader and tests, drop the `rdkit` dependency, and add the detail endpoint to the CompTox configuration.
- **BREAKING (internal):** the `smiles-lookup` capability, the PubChem settings and the RDKit dependency no longer exist; molecular weight is reported with source "CompTox" instead of "calculated".

## Capabilities

### New Capabilities
(none)

### Removed Capabilities
- `smiles-lookup`: CAS-to-SMILES resolution through PubChem is no longer needed.

### Modified Capabilities
- `comptox-property-lookup`: DTXSID is resolved from the CAS number with exact-match verification instead of from a SMILES, and the chemical's average molecular mass is made available.
- `comptox-toxicity-lookup`: corrected labels, exposure-route filter, conservative selection within the best source, CAS-based shared lookup.
- `chemical-properties-tool`: all data, including molecular weight, is fetched from CompTox by CAS.
- `app-configuration`: CAS-search endpoint, per-entry routes and preference, corrected defaults; PubChem settings removed.

## Impact

- Changed: `tools/informatics/helpers/comptox.py`, `tools/informatics/properties.py`, `config/settings.toml`, `config/loader.py`, `config/__init__.py`, `pyproject.toml` and `uv.lock` (rdkit removed), new `tools/informatics/helpers/cas.py`, and the matching tests plus `tests/smoke/`.
- Deleted: `tools/informatics/helpers/smiles.py` and its test, `openspec/specs/smiles-lookup/` (on archive).
- Dependency removed: `rdkit`. No new dependencies.
- Ordering: `chemical-properties-tool` and its configuration additions come from the not-yet-archived `implement-fetch-chemical-properties`; archive that change first, then this one.
- Evidence for the data claims: live responses for benzene, toluene, formaldehyde and carbon tetrachloride (route, subtype, qualifier and human/eco fields were inspected; `qualifier` was always `=` and `humanEco` always human health, so no filters are added for them).
