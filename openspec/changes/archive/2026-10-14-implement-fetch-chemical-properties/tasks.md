## 1. Configuration

- [x] 1.1 Add `target_unit` to each `[[comptox.properties]]` (vapor_pressure mmHg, density g/cm^3) and `[[comptox.toxicity_values]]` (rfd mg/(kg*day), rfc mg/m^3, sf 1/(mg/(kg*day)), iur 1/(ug/m^3)) in `config/settings.toml`, and add a `[units.aliases]` table
- [x] 1.2 Add `target_unit` (required) to `PropertySpec` and `ToxicityValueSpec`; add `UnitSettings`, `load_unit_settings` and `get_unit_settings` to `config/loader.py`
- [x] 1.3 Update and extend `tests/config/test_loader.py`: target unit required, aliases loaded, missing alias table gives none, non-string alias rejected, defaults contain the four toxicity and two property target units

## 2. Unit conversion

- [x] 2.1 Create `commons/units.py` with `UnitConversionError` and `convert(value, from_unit, to_unit, aliases)` using a module-level Pint registry; export from `commons/__init__.py`
- [x] 2.2 Create `tests/tools/informatics/helpers/test_units.py`: ug/m^3 to mg/m^3, same unit, reciprocal units, mmHg to Pa style factor, dimension mismatch, unknown unit, NaN/inf, alias on source and on target, every configured target unit parses

## 3. Molecular weight

- [x] 3.1 Add `molecular_weight(smiles)` (g/mol, None for unparsable) to `tools/informatics/helpers/smiles.py` and test it with a simple structure whose mass is computed independently in the test

## 4. Types

- [x] 4.1 Replace `ChemicalProperties` in `tools/schemas.py` with `molecular_weight, vapor_pressure, density, rfd, rfc, sf, iur` (`float | None`, units in comments), `sources: dict[str, str]` and `warnings: list[str]`

## 5. Tool

- [x] 5.1 Implement `lookup_chemical_properties` in `tools/informatics/properties.py`: CAS -> SMILES -> molecular weight -> CompTox properties and toxicity -> conversion to target units, with warnings and sources per the spec
- [x] 5.2 Implement the `@tool` `fetch_chemical_properties` wrapper with lazily built, cached default collaborators and a docstring listing fields, units and None/warnings/sources semantics
- [x] 5.3 Replace the stub test in `tests/tools/informatics/test_properties.py` with tests using fake lookups: all values present and converted, unit conversion applied, incompatible unit gives None plus warning, missing value warning, unresolvable and blank CAS, missing API key raises, schema/description checks
- [x] 5.4 Confirm `tests/tools/test_registry.py` still passes; update README if it describes the tool as a stub

## 6. Verification

- [x] 6.1 Run `uv run ruff format .`, `ruff check .`, `pyright`, `pytest`, and the bandit command; confirm no example files or keys are staged
- [x] 6.2 With the user's go-ahead, run the tool once against a real CAS number (e.g. benzene) to check CompTox unit spellings and ToxVal labels, and adjust aliases or labels in config if they differ
