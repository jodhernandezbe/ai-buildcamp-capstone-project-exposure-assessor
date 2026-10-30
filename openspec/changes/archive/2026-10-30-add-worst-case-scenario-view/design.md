## Context

See proposal.md for why. Today `tools/assessment` builds, per facility, a `FacilityExposure` with one `StackExposure` per stack (concentration, distance, stability, wind speed, release height, HQ, cancer risk, per-band dose, stack source) and a `range` that already names `low_stack` / `high_stack`. The population step returns a pooled count and age mix; `census.py` asks TIGERweb for the tracts that intersect the circle with `returnGeometry=false` and keeps only the codes and land area. The worker result (`occupational_exposure`) holds both ventilation tiers. The workspace projectors (`api/services/projectors`) turn tool artifacts into `Facility`, and the ribbon, inspector and Risk by group read it.

Checked live: the same TIGERweb request returns each tract's internal point (`INTPTLAT`, `INTPTLON`, signed strings, e.g. `+18.1551099`, `-065.9466749`), so tract distance and bearing need no new request.

The worst-case weather of a screening run has no wind direction (it is the SCREEN3 combination that maximizes the concentration anywhere between 100 m and 10 km), so a worst-case receptor cannot be chosen by sector; it can be chosen by distance.

## Goals / Non-Goals

**Goals:**
- One generic worst-case scenario shape for every pathway, current and future, built only from values already computed.
- Receptors ranked by the concentration the scenario itself gives at their distance.
- The UI leads with the driving scenario; everything else is behind an explicit control.

**Non-Goals:**
- New dispersion physics, a plume footprint, population inside a downwind sector for the representative weather (the schematic sector on the map stays schematic).
- Screening-out changes. Worker results for screened-out facilities remain a separate decision (they are not computed today and this change does not change that).
- Changing the system prompt.
- Changing `add-exposure-chain-visualizer`; it can read the scenario later.

## Decisions

1. **Receptors by concentration at distance, not by sector.** For the community scenario, evaluate the scenario's stability, wind speed, release height and rate at each tract's distance with the existing dispersion equations (new pure function in `models/`, equal to the maximum at the maximum's distance), rank tracts by it, and list those at or above a configured fraction of the maximum (default 0.5), capped by a configured count. Alternatives: a downwind sector (needs a wind direction the worst case does not have, and would invent one); a distance ring around the maximum (ignores that concentration falls on both sides). Bearing is reported and drawn but does not select.
2. **Tract points from TIGERweb, not geometry.** Add the internal-point fields to the existing `[population]` field map and parse them into `Tract`; the per-tract list is returned next to the unchanged pooled result. Tract residents are the ACS counts of the tract (not area-scaled), labelled as such, because the area scaling belongs to the pooled count. Alternative: request polygons (larger payload, new geometry code).
3. **A generic scenario and a registry of pathways.** A scenario is `{pathway, quantity, value, unit, tier, benchmark, facility, factors[], receptors[], notes}`; a factor is `{key, label, group, value, unit, source | reason}` with groups `source`, `release`, `conditions`, `receptor_model`. Each pathway is one module in `tools/assessment/helpers/scenarios/` exposing a builder, listed in a `PATHWAYS` registry (as `LANES` does for the exposure graph); its labels, units and the pathway name are configuration. The API and the UI render factors and receptors generically, so a new pathway (dermal, ingestion, a water route) is a new module plus configuration. The scenario states the tier the assessment gave and never a regulatory finding such as "unreasonable risk". Alternative: fixed fields for stack and weather (simple today, a schema and UI change for every new pathway).
4. **The scenario is built in `tools/assessment`, not in `api/`.** `api/` only rearranges tool values (its rule), so the assessment composes the scenario from the stack results, the tracts and the worker result in one helper module and returns it in the artifact; the projector validates and files it. Alternative: build in the projector (violates the api rule, duplicates selection logic).
5. **The driver is chosen by value among assessed facilities,** per pathway and quantity, with the stack from `high_stack`. Ties go to the facility listed first by the assessment's existing order. Screened-out and worst-case-only facilities are not drivers of receptor lists, but a worst-case-only facility keeps a scenario without receptors.
6. **Worker scenario reuses the occupational result.** The result is extended to name the ventilation tier with the highest ratio and the schedule used; workers are the receptors. No new equation.
7. **UI: lead with the driver, close the rest.** The ribbon cards each show one driving scenario; "Other facilities" is a closed disclosure. The inspector shows the scenarios first and marks the driving stack. Risk by group tooltips name the facility and stack. The map marks the driving facility and draws receptors only for the selected driver. This is a requested change to the Overview and Map panels.
8. **Contract and cassettes.** New wire models in `api/schemas/workspace.py`, regenerated types, a store default for older servers (as for the worker fields), and the full-assessment cassettes re-recorded (population output gains tracts).

## Risks / Trade-offs

- [The worst case may fall where no one lives] → a stated outcome, with the nearest populated tract and its fraction of the maximum, never an empty list.
- [Tract internal points are one point per tract, so distance is approximate for large tracts] → label receptors as tracts, show the tract's land area, and keep the fraction threshold coarse; do not claim individual exposure.
- [Tract residents are not area-scaled while the pooled count is] → label them "residents of the tract" and keep the pooled count unchanged.
- [Payload growth from tract lists across many facilities] → cap tracts per facility by configuration and ship the listed receptors only for the driver and the top facilities.
- [A generic shape could become a bag of strings] → factors keep a typed value and unit, a group and a source or reason, and the contract is validated per factor.
- [Cassette and eval churn] → re-record the full-assessment scenarios and run the evals three times; the prompt is untouched.

## Open Questions

- Default for the fraction (0.5) and the receptor cap (10) are starting values to confirm against real facilities once the tract list exists.
