## Why

Every assessment today answers one question: what do people living near the fence line breathe
(SCREEN3 plume from the TRI stack release). TRI also reports **fugitive air** releases, which
evaporate inside or beside the plant and mainly expose the **workers**, and the app already
touches the data to size that exposure: the Census QPC plant-hours baseline, the TSCA
conditions of use derived from TRI Section 3, and the PubChem record. Adding a worker
screening (EPA ChemSTEER box model, RAGS Part F style dosimetry) lets a user see whether a
facility's risk is driven by the stack plume (community) or indoor evaporation (worker),
without any new paid or scraped source.

## What Changes

- **Fugitive release in the inventory.** The TRI query also returns `AIR FUG` per facility
  (a configured medium, one more query per medium) and each facility record carries its
  fugitive release (kg/yr) beside the stack release. The stack path and its numbers do not change.
- **Operating schedule.** The existing Census QPC lookup also yields a schedule: hours per
  week (from the baseline), days per week, hours per day, operating days per year and annual
  operating hours (`t_op`, capped at 8,760 h). `annual_operating_hours` is recorded in the
  emission-rate provenance. Days per week is not in the QPC file, so it is a configured rule,
  not a per-NAICS table of invented numbers (see design).
- **TSCA condition of use + CDR industrial sector.** A new NAICS to CDR industrial sector
  crosswalk file (version-controlled, sourced from EPA's CDR instructions) gives the `IS` code;
  life cycle stage and condition of use keep coming from the TRI Section 3 activities the
  inventory already maps. No sector is guessed: unmatched means null with a reason.
- **PubChem occupational limits.** The PUG View parser also reads OSHA PEL, NIOSH REL, ACGIH
  TLV (TWA and STEL), NIOSH IDLH and the PAC-1/2/3 values from "Exposure Control and Personal
  Protection", normalises ppm to mg/m3 at 25 degC and 1 atm with the molecular weight, and picks
  the 8-hour TWA benchmark in the order OSHA PEL, NIOSH REL, ACGIH TLV. Headings are configured.
- **Occupational model.** New pure module `models/exposure/occupational.py`: ChemSTEER
  mass-balance box (two ventilation tiers), 8-hour TWA and OEL ratio, RAGS Part F worker
  ADC/LADC, HQ and cancer risk, and the `exceedance` / `elevated` / `acceptable` tier.
- **Assessment result and workspace.** Each assessed facility returns `community_exposure`
  (today's `exposure`, unchanged), `occupational_exposure` and `operational_profile`; the
  workspace SSE payload and its generated TypeScript types carry the latter two.
- **Frontend.** The Overview panel gets a Community / Occupational switch with the profile
  badges and worker numbers; the map hover card gets a compact occupational badge next to
  the community HQ. These two panels change because the request asks for it.

## Capabilities

### New Capabilities
- `occupational-exposure-model`: the ChemSTEER box, 8-hour TWA / OEL ratio, RAGS Part F worker
  dose, HQ, cancer risk and risk tier, as pure arithmetic with unit and input validation.
- `pubchem-occupational-limits`: reads and normalises OSHA/NIOSH/ACGIH/IDLH/PAC limits from a
  PUG View record and chooses the TWA benchmark with its source.
- `operating-profile`: a facility's operating schedule and its TSCA life cycle stage,
  condition of use and CDR industrial sector, with sources and no guessing.
- `occupational-exposure-tool`: the per-facility occupational screening that joins the fugitive
  release, the schedule, the limits and the toxicity values into `occupational_exposure`.

### Modified Capabilities
- `plant-operating-hours`: the match also yields the schedule fields and states them in the source.
- `emissions-inventory-tool`: fugitive air medium; fugitive release on the record;
  `annual_operating_hours` in the emission-rate provenance.
- `facility-assessment-tool`: every assessed facility carries community, occupational and
  profile results; the screening tiers are unchanged and still driven by the community bound.
- `assessment-dashboard-state`: facilities carry `occupational_exposure` and `operational_profile`.
- `web-ui-shell`: Overview Community/Occupational view and hover-card occupational badge.

## Impact

- Code: `models/exposure/`, `tools/exposure/`, `tools/emissions/` (inventory, plant hours),
  `tools/informatics/helpers/pubchem/`, `tools/assessment/`, `tools/schemas.py`, `config/`
  (`settings.toml` plus typed loaders), `api/schemas/workspace.py` and projectors,
  `frontend/src/features/overview` and `features/map`, generated `frontend/src/types`.
- Data: one new reference CSV (NAICS to CDR industrial sector); the Census baseline is reused.
- Costs: one extra TRI request per chemical for the fugitive medium; no new service or key.
- Paths in the request that differ from the repo (`tools/chemicals/pubchem_client.py`,
  `tools/emissions/operating_schedule.py`, `models/occupational.py`, `EPAExecutiveOverview.tsx`,
  `/api/v1/chat/stream`) are mapped to the existing layout in the design.
- Screening estimates only; not an OSHA compliance determination.
