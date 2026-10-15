## Context

`ComptoxLookup` (`tools/informatics/helpers/comptox.py`) already does SMILES -> DTXSID -> property summary with an injectable client, sleep and environment, and caches results per SMILES. `ComptoxSettings` in `config/loader.py` carries the endpoints and the `[[comptox.properties]]` list. The ToxVal endpoint (`hazard/toxval/search/by-dtxsid/{dtxsid}`) returns a flat JSON list of records; the fields used here are `toxvalType`, `toxvalNumeric`, `toxvalUnits` and `source`. See proposal.md - Impact for the unverified-label caveat: `example.json` has none of the target types (it has NOAEL, LOAEL, LEL, NEL, MEG, PAC).

## Goals / Non-Goals

**Goals:**
- `ComptoxLookup.get_toxicity_values(smiles)` returning configured toxicity values with unit and source.
- Everything that varies (endpoint, labels, source order) in config.

**Non-Goals:**
- Unit conversion or reconciling route (oral vs inhalation); the type label already implies the route (RfD/SF oral, RfC/IUR inhalation).
- Filtering by study, species, qualifier or QC category; deriving values from NOAEL/LOAEL.
- Wiring `fetch_chemical_properties` to the helper.

## Decisions

1. **Same class, new method.** Add `get_toxicity_values` to `ComptoxLookup` rather than a second class, since DTXSID resolution, auth and failure handling are shared. Alternative: a separate `ToxValLookup`; rejected because it would duplicate that logic or force sharing through a third object.
2. **DTXSID cache.** Cache the DTXSID per SMILES (hits and definitive misses) so `get_properties` followed by `get_toxicity_values` sends one DTXSID search. Property and toxicity results keep separate caches, so a failure in one never poisons the other.
3. **Config shape.** Add `toxval_by_dtxsid_path` (with `{dtxsid}`) to `[comptox]`; `source_priority = ["IRIS"]`; and `[[comptox.toxicity_values]]` tables with `key` and `types` (list of accepted `toxvalType` labels), initially `rfd -> ["RfD"]`, `rfc -> ["RfC"]`, `sf -> ["SF", "OSF"]`, `iur -> ["IUR"]`. Loader gains `ToxicityValueSpec`, and `ComptoxSettings` gains `toxval_by_dtxsid_path`, `toxicity_values` and `source_priority`. Validation mirrors the property list (non-empty strings, non-empty `types`, unique keys, `{dtxsid}` placeholder). `toxicity_values` may not be empty, matching `properties`. Alternative: reuse `[[comptox.properties]]` with a `kind` field; rejected because the two endpoints have different record shapes and selection rules.
4. **Matching.** Exact, case-sensitive match of `toxvalType` against the accepted labels; records whose `toxvalNumeric` is not a real number (null, string, bool) are skipped. Skipped-because-no-match types are logged at debug.
5. **Selection.** Among matches, minimum by (index of `source` in `source_priority`, or its length if unlisted); stable, so ties keep API order.
6. **Result type.** `ToxicityValue` TypedDict in `tools/schemas.py`: `value: float`, `unit: str`, `source: str` (database name, e.g. a ToxVal source), with units documented as reported. Kept distinct from `PropertyValue`, whose `source` is a fixed experimental/predicted literal.
7. **Request count.** Two requests per uncached chemical for toxicity (DTXSID, ToxVal), each preceded by the configured delay; zero extra DTXSID requests when properties were already fetched.

## Risks / Trade-offs

- [Label strings in live data may differ from RfD/RfC/OSF/SF/IUR] -> Labels are config; debug log lists the distinct `toxvalType` values seen when nothing matched. Verify against a chemical that has these values during apply.
- [Same type may carry different units across sources, e.g. IUR per ug/m3 vs per mg/m3] -> Unit passed through and source reported; downstream must check units before use.
- [The "IRIS" source string is a guess] -> Unlisted sources still work as fallback, so a wrong name degrades to API order, not to missing values.
- [Large ToxVal responses (many records per chemical)] -> One pass over the list per call; results cached per SMILES.
