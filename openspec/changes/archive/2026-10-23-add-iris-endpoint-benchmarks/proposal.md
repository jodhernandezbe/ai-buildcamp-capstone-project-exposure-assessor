## Why

ToxVal is a secondary copy of the assessments. Comparing it with CompTox's own IRIS endpoint
(`/hazard/iris/search/by-dtxsid/{dtxsid}`) showed that the endpoint is more current and more
direct: for formaldehyde IRIS (revised 2024) gives an RfC of 0.007 mg/m3, but ToxVal has no IRIS
RfC for it, so the tool reports 0.0098 mg/m3 from EPA RSL. Where both exist, the values match
(benzene, hexane, toluene, naphthalene, DBCP, acrolein). The endpoint also names the target
organ systems and tumor sites, which the report can state.

## What Changes

- Read the IRIS endpoint for each chemical and use its chronic RfD and RfC as the top-ranked
  source for `rfd` and `rfc`, ahead of every ToxVal source. `iur` and `sf` stay with ToxVal
  (the endpoint has none).
- Parse the endpoint's text values (`"4 x 10 -3 mg/kg-day"`, `"5 mg/m3"`) with a strict reader
  that refuses anything it cannot read exactly (ranges, several values, missing units).
- When ToxVal also has an IRIS record for the same field and the two differ by more than a
  configured tolerance, use the endpoint's value and add a warning naming both.
- Report the critical-effect systems as the endpoint of the value, with source
  `EPA IRIS: IRIS (CompTox IRIS endpoint)` and its last significant revision date.
- Configure the path, the response fields, the units and the tolerance in
  `config/settings.toml`.

Out of scope: subchronic values, the ToxRef endpoints (study-level animal data; no benchmarks and
no coverage for most of our chemicals), IUR/SF, changing the model-facing tool description
(wording changes destabilised the agent evaluation).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `comptox-toxicity-lookup`: IRIS-endpoint values take precedence for RfD and RfC; how they are
  read, checked and reported.

## Impact

- `config/settings.toml` and `config/loader.py` (an `[comptox.iris]` table),
  `tools/informatics/helpers/comptox.py` (one more request per chemical, a parser module),
  `tools/schemas.py` only if a revision field is added to the toxicity detail.
- Behavior: some `rfc`/`rfd` values change source and value (formaldehyde RfC 0.0098 -> 0.007);
  one extra CompTox request per chemical.
- Tests: parser (positive and negative), precedence, disagreement warning, failure handling;
  live check on formaldehyde and benzene; evals re-run.
