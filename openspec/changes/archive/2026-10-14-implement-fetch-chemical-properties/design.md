## Context

Building blocks exist: `SmilesLookup.get_canonical_smiles(cas)`, and `ComptoxLookup.get_properties(smiles)` / `get_toxicity_values(smiles)`, which return values in whatever unit CompTox reports (helper specs require no conversion there). `models/risk.py` documents the units it needs: RfD mg/(kg*day), RfC mg/m^3, SF (mg/(kg*day))^-1, IUR (ug/m^3)^-1. `pint` and `rdkit` are already dependencies. Tool rules: no LLM calls, no imports from `agent/`, TypedDict outputs, rich docstring, no hard-coded values that belong in `config/`. See proposal.md for scope.

## Goals / Non-Goals

**Goals:**
- A working `fetch_chemical_properties` with fixed output units and explicit missing-data signalling.
- A reusable converter that cannot silently pass through a wrong-dimension value.

**Non-Goals:**
- Temperature correction of vapor pressure (source value is used as reported, typically near 25 C).
- Choosing between PubChem and CompTox for molecular weight; it is computed.
- Retrying failed requests, or surfacing per-source detail beyond one source label per field.

## Decisions

1. **Conversion lives in the tool layer, not the CompTox helper.** `ComptoxLookup` keeps returning source units (its specs say so); `commons/units.py` provides `convert(value, from_unit, to_unit, aliases)`, and the tool applies it. The converter knows nothing about CompTox, so it lives in the shared `commons/` package (importable from any layer, taking aliases as a parameter) rather than under `tools/informatics/`. Alternative: convert inside the helper; rejected because it would change published helper behavior and hide the source unit.
2. **Pint usage.** One module-level `UnitRegistry`. Aliases are applied by exact string lookup on the stripped reported unit (and on the target) before `registry.Quantity(value, unit).to(target)`. Failures (`UndefinedUnitError`, `DimensionalityError`, parse errors, non-finite input) are wrapped in one `UnitConversionError(ValueError)` whose message names both units. Multiplicative units only; offset units (degC) are not needed for these fields and Pint's offset handling is left untouched.
3. **Config.** `target_unit` is added to each `[[comptox.properties]]` and `[[comptox.toxicity_values]]` table (`PropertySpec`, `ToxicityValueSpec` gain the field, required). A new `[units.aliases]` table maps source spellings to Pint-parsable strings; `UnitSettings` and `load_unit_settings` / `get_unit_settings` mirror the existing loader pattern (missing table = no aliases; values must be non-empty strings). Initial aliases cover the likely CompTox forms: `mg/m3`, `ug/m3`, `mg/kg-day` and the reciprocal spellings `(mg/kg-day)-1`, `(ug/m3)-1`. Unverified against live data, so unknown spellings degrade to a warning.
4. **Molecular weight.** `smiles.py` gains `molecular_weight(smiles) -> float | None` using RDKit's average molecular weight (g/mol); a SMILES RDKit cannot parse returns None. It is not configurable because it has no external source.
5. **Orchestration function, thin tool.** `lookup_chemical_properties(cas, smiles_lookup, comptox, comptox_settings, unit_settings) -> ChemicalProperties` holds the logic and takes its collaborators as arguments, so tests need no patching. The `@tool` function builds module-level default instances lazily (cached) and calls it. Alternative: build everything inside the tool; rejected as hard to test and it would recreate HTTP clients per call, losing caches.
6. **Output shape.** `ChemicalProperties` fields: `molecular_weight, vapor_pressure, density, rfd, rfc, sf, iur: float | None`, `sources: dict[str, str]`, `warnings: list[str]`. The tool maps result keys to fields by a fixed mapping in the tool module (`vapor_pressure`, `density`, `rfd`, `rfc`, `sf`, `iur`); a config entry whose key has no field is ignored with a warning-free debug log, since adding a *new* output field also needs a schema change. This keeps the TypedDict explicit (project rule) at the cost of one code edit per new output field.
7. **Missing vs failure.** A field absent from the helper result gets "<field> not found in CompTox". The helpers return `{}` for both "no data" and "service failure", so the tool cannot tell them apart; the warning text for an entirely empty CompTox result is therefore "no CompTox data retrieved (not found or service unavailable)". Alternative: change the helpers to report failures; deferred, listed under Risks.
8. **Errors.** A missing API key still raises (propagated `RuntimeError` from the helper). An unresolvable CAS returns the all-None result with a warning, without contacting CompTox or needing the key.
9. **Docstring fidelity.** The tool docstring lists each field, unit and the None/warnings/sources semantics; vapor pressure is documented "mmHg, as reported by the source (typically 25 C)".

## Risks / Trade-offs

- [Helpers cannot distinguish "no data" from "service down"] -> One combined warning; a later change can have the helpers return a status.
- [Alias table guesses CompTox spellings] -> Unknown spellings produce warnings, never wrong numbers; add aliases when seen.
- [Pint may accept a unit that parses to the right dimension but a different meaning, e.g. "mmHg" vs "torr"] -> Only dimension-compatible conversions pass; magnitudes use Pint's definitions, covered by tests with exact factors.
- [One schema field per output property requires code edits] -> Accepted to keep strict typing.
- [Module-level default instances persist HTTP client and caches across calls] -> Intended (caching, rate limiting); tests inject their own.
