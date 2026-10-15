## Why

The risk step (`models/risk.py`) needs a reference dose (RfD), reference concentration (RfC), oral slope factor (SF/OSF) and inhalation unit risk (IUR), and the `fetch_chemical_properties` stub promises RfC and IUR. The CompTox helper already resolves a SMILES to a DTXSID and reads physical-chemical properties, but it cannot return toxicity values. CompTox's ToxVal endpoint serves them by DTXSID.

## What Changes

- Extend the CompTox helper with a toxicity lookup: SMILES -> DTXSID (reused, now cached so a second lookup does not repeat it) -> ToxVal records for that DTXSID.
- Select the records whose `toxvalType` matches each configured toxicity value (RfD, RfC, SF/OSF, IUR), keep those with a numeric `toxvalNumeric`, and return the value, `toxvalUnits` and the record's `source`.
- When several records match, pick by an ordered source-priority list in config; sources not listed rank after listed ones.
- Add to the `[comptox]` config: the ToxVal endpoint path and a list of toxicity values to extract (result key, accepted `toxvalType` labels), plus the source-priority list. Adding another toxicity value is a config edit.

## Capabilities

### New Capabilities
- `comptox-toxicity-lookup`: extract configured toxicity values (RfD, RfC, SF, IUR) with units and source from CompTox ToxVal records.

### Modified Capabilities
- `app-configuration`: CompTox settings also cover the ToxVal endpoint, the toxicity value list and the source-priority list.

## Impact

- Changed: `tools/informatics/helpers/comptox.py`, `config/settings.toml`, `config/loader.py`, `tools/schemas.py` (new `ToxicityValue` payload), and the matching tests.
- No new dependencies; `fetch_chemical_properties` stays a stub.
- Assumption to verify at apply time: `example.json` (phenolphthalein) contains no RfD/RfC/IUR/SF records, so the `toxvalType` labels come from the request ("RfD", "RfC", "OSF"/"SF", "IUR") and are matched exactly. If live data labels them differently (e.g. "cancer slope factor"), add the label to the config list. Likewise the initial source-priority entry ("IRIS") is unverified.
