## Why

The batch assessment screens every facility with the AirToxScreen global default stack, then
refines (own NEI stacks, else PSTK by SCC, else that same default) only the first
`max_refined = 500` facilities whose bound reaches a threshold, largest bound first. The rest are
dropped from what the dashboard receives, so for a chemical like benzene (844 facilities) hundreds
show up on the map with no stacks, no screening and no status, and their card says "Not assessed
yet: no stack parameters were obtained", which is wrong twice: nothing failed, and the global
default stack (the fallback that is never missing) was available for every one of them. The
project's own principle is to exclude a facility only on a conservative bound, never by emission
rank; a cap by rank breaks it. Every facility should be assessed unless there is no fallback.

## What Changes

- Refine **every** facility whose bound reaches a threshold: own NEI stacks, else PSTK by SCC, else
  the global default. `max_refined` stops being a ranking cut. It stays only as a documented,
  high safety bound (5,000) that, when hit, is reported with the facilities beyond it carried as
  not assessed, never silent.
- Keep the cap on the **full chain** with weather and Census (`max_facilities = 25`, a request-cost
  limit); the facilities beyond it stay at worst case only, as today. Facilities asked for by FRS
  ID beyond that cap are also kept at worst case only instead of being dropped.
- Carry the not-assessed facilities, with their reasons, in the artifact the program receives
  (`AssessmentArtifact.not_assessed`) and show them in the workspace as a screening outcome
  `not_assessed` with the reason, so the card says the real reason, and a facility the batch never
  covered says that instead of "no stack parameters were obtained".
- Make the same-site (twin) search for EIS IDs **bulk**. It was the real cost of assessing
  hundreds of facilities: one request per facility (about 4.5 s each, four at a time). It
  becomes one request per batch of names, so it no longer limits how many facilities can be
  assessed.
- **BREAKING (tool contract):** `AssessmentArtifact` gains `not_assessed`; the API `Screening`
  outcome gains `not_assessed`; `[assessment].max_refined` changes meaning and value.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `facility-assessment-tool`: tiered screening without the tier-2 ranking cut; facilities by ID
  beyond the full-chain cap kept at worst case; not-assessed facilities in the artifact.
- `assessment-dashboard-state`: a facility the batch left unassessed carries that outcome and its
  reason; the card says it.
- `emissions-inventory-tool`: same-site EIS searches in bulk.

## Impact

- Code: `tools/assessment/` (`helpers/tiers.py`, `facilities.py`, `helpers/view.py`),
  `tools/schemas.py`, `config/assessment.py` and `settings.toml`;
  `tools/emissions/helpers/inventory/eis.py` and `[frs_eis]`; `api/schemas/workspace.py`,
  `api/services/projectors/assessment.py`, the exported contract and frontend types;
  `frontend/src/features/map/FacilityHoverCard.tsx` and `features/overview/assessment.ts`.
- Behavior: more facilities get stacks, a worst case and a status (their markers gain colour);
  results for the facilities that were already refined do not change.
- Cost (measured on live benzene, 844 facilities, see the design): refining all of them is about
  5 s of compute; the EIS twin searches were the cost, about 15 minutes at one request per
  facility, a minute or so in bulk.
- Dependencies: none. The evals' recorded tool outputs are unaffected in shape except the new
  artifact field; re-recorded only if replay breaks.
