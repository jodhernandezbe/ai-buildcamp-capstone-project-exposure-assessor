## Context

See proposal.md. `ComptoxLookup.get_toxicity_values` fetches the ToxVal records of the DTXSID and
`select_toxicity` ranks them by the configured source order. The IRIS endpoint returns a list
with one record: `rfdChronic`, `rfcChronic` (and subchronic) as free text, `criticalEffectsSystems`
(newline-separated systems), `tumorSite`, `lastSignificantRevision`, `irisUrl`. The shared lookup
rules (key, retries, caching of definitive answers only, copies) apply.

## Decisions

- **Endpoint as the top source, not as a ToxVal record.** The endpoint's value is turned into a
  `ToxicityValue` and placed ahead of ToxVal's choice for `rfd` and `rfc`. Alternative: only a
  fallback when ToxVal has nothing; rejected: it would leave formaldehyde's RfC at 0.0098 mg/m3
  (RSL), and IRIS is the reference source the project already ranks first.
- **A separate parser module** (`helpers/iris_text.py`): one regex for `number [x 10 exp] unit`,
  anchored, so anything else is refused; the unit goes through the existing unit converter
  (aliases cover `mg/kg-day`, `mg/m3`). Negative tests for each refused shape.
- **Config:** `[comptox.iris]` with `path`, per-field `{key, field, route, target_unit}` entries
  (rfd -> rfdChronic, rfc -> rfcChronic), and `agreement_tolerance` (relative, for the warning).
  A further field is a table entry.
- **Cache and failure:** same per-CAS cache as ToxVal; the endpoint request has its own
  "definitive" flag, so its failure is not cached and does not hide ToxVal values.
- **Reporting:** `endpoint` = the systems joined with ", " (the specific effect text stays a
  ToxVal-only detail); revision date added to the source string or to a new optional
  `ToxicityDetail` field (decide at implementation; see open questions).

## Risks / Trade-offs

- [Free-text values change format] -> strict parser plus a live smoke test; refused text falls
  back to ToxVal with a warning.
- [One more request per chemical] -> small; the delay and retries already apply.
- [Two IRIS copies disagree] -> the endpoint wins and the disagreement is warned.

## Resolved Questions

- **Tumor site:** not surfaced. Slope factor and unit risk stay with ToxVal, which already reports
  the cancer endpoint; surfacing the endpoint's `tumorSite` would need a second source of the same
  fact. A later change can add it.
- **Revision date:** in the source string (`source_revised` in `[comptox.iris]`), so the API
  contract and the frontend types do not change.
- **Where notes go:** `ComptoxLookup.get_toxicity_notes(cas)` returns the refused-text and
  disagreement notes of the last lookup; `fetch_chemical_properties` appends them to `warnings`.
- **Accepted units:** listed per field in the settings and matched exactly (`mg/kg-day`,
  `mg/m3`); the value is returned in the unit written and converted later, like every other value.
- **Optional table:** a settings file without `[comptox.iris]` leaves the endpoint unused.
