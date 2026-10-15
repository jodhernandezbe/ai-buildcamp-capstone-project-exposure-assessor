## Why

`fetch_chemical_properties` is the first tool the agent calls, and it is still a stub that raises `NotImplementedError`. Its building blocks now exist (CAS -> SMILES, SMILES -> CompTox properties and toxicity values), but CompTox reports units as it finds them, and the risk models in `models/risk.py` need fixed units. A unit mismatch would silently produce wrong hazard quotients and cancer risks, so conversion must be a guardrail, not an afterthought.

## What Changes

- Implement `fetch_chemical_properties(cas_number)`: CAS -> canonical SMILES -> molecular weight (computed from the structure) plus CompTox properties and toxicity values, returned in fixed target units.
- Add a unit-conversion guardrail built on Pint: every CompTox value is converted to its configured target unit; a value that cannot be converted (unknown unit, wrong dimensionality) is never returned as-is, but reported as missing with a warning.
- Extend the tool output (`ChemicalProperties`) to molecular weight, vapor pressure, density, RfD, RfC, SF and IUR. Each is `None` when unavailable; a `warnings` list explains why, and a `sources` map records where each value came from.
- Put target units and a unit-alias table (CompTox spellings such as `mg/m3` -> Pint-parsable forms) in `config/settings.toml`, so a new property or unit spelling is a config edit.

## Capabilities

### New Capabilities
- `chemical-properties-tool`: the agent-facing tool that resolves a CAS number and returns screening properties and toxicity values in fixed units with warnings and sources.
- `unit-conversion`: Pint-based conversion to a target unit with dimensionality checking and configurable unit-spelling aliases.

### Modified Capabilities
- `app-configuration`: each CompTox property and toxicity entry carries a target unit, and the configuration holds a unit-alias table.

## Impact

- New: `commons/units.py`; tests for it and for the tool.
- Changed: `tools/informatics/properties.py`, `tools/informatics/helpers/smiles.py` (molecular weight), `tools/schemas.py` (`ChemicalProperties`), `config/settings.toml`, `config/loader.py`, existing tests (the stub test is replaced), `README.md` if it describes the stub.
- No new dependencies: `pint` and `rdkit` are already in `pyproject.toml`.
- **BREAKING (internal):** `ChemicalProperties` changes shape (new fields, optional values, `warnings`, `sources`). Nothing else in the repo consumes it yet.
- Unverified: CompTox's unit spellings for RfD, RfC, SF and IUR are not in any sample we have; the alias table starts from likely forms, and any spelling it does not know yields a warning rather than a wrong number.
