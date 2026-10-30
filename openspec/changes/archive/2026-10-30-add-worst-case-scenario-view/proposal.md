## Why

The dashboard lists every stack, every age band and a pooled population, so a reader cannot see what actually produces the high-end value. An EPA-style screening result is defined by the combination of factors behind it: which facility, which stack configuration, which weather and distance, and who is there. Today the facility, the stack and the weather are in the tool results but not presented as one scenario, and the receptors are only a pooled count in a radius, so nobody can say which residents the worst case reaches (the tool itself warns that "the worst case may fall where no one lives").

## What Changes

- Define a **worst-case scenario** in one generic shape for every exposure pathway: the pathway (medium, route, receptor class), the result quantity and its high-end value, the benchmark and tier it was compared with, the facility, a list of factors (source, release, conditions, receptor model, each with value, unit and source or a reason) and the receptors. Today that covers outdoor air → inhalation → general population (hazard quotient, cancer risk) and indoor air → inhalation → worker (limit ratio, hazard quotient, cancer risk); a **registry of pathways** lets a future pathway (another route or medium) add its scenario without changing the shape, the projection or the display. A scenario is the evidence of the combination of factors behind a value that exceeds a level of concern; it never states that a risk is "unreasonable" (that is a regulatory determination).
- The population step returns the **residents by Census tract with each tract's distance and bearing** from the facility, in addition to the pooled totals it returns today.
- Under a community worst-case scenario, **rank the receptors**: evaluate the scenario's own configuration (same stability, wind speed, release height) at each tract's distance and report the tracts, with their age bands, that are exposed most, or say that no one lives within the reach of the maximum. For workers, the receptors are the workers of the driving facility.
- The ribbon, the facility inspector and the Risk by group charts **show the driving scenario** (and its receptors) instead of every facility, stack and population; the rest stays available behind an explicit "other facilities and stacks" control.
- No new data source and no new physics: the scenario is a presentation of values the tools already compute, plus per-tract distance, bearing and the concentration at that distance from the existing dispersion equations.

## Capabilities

### New Capabilities
- `worst-case-scenario`: the generic scenario shape (pathway, quantity, tier, factors, receptors), the registry that produces scenarios per pathway, how the driver is chosen, and that it is stated only from tool values.

### Modified Capabilities
- `population-receptors-tool`: also returns the tracts with population, age bands, distance and bearing from the point.
- `population-estimation-model`: tract distance and bearing from the facility, and the share of a tract inside the radius.
- `screening-dispersion-model`: concentration at a stated downwind distance for a fixed scenario configuration.
- `facility-assessment-tool`: each assessed facility carries its worst-case scenarios and the ranked receptors.
- `occupational-exposure-tool`: the worker scenario (fugitive release, ventilation tier, shift) behind the highest ratio.
- `assessment-dashboard-state`: the workspace projects the scenarios and their receptors, and which facility drives each.
- `web-ui-shell`: the ribbon, inspector and Risk by group show the driving scenario; the others are collapsed.

## Impact

- `models/`: a distance-and-bearing function and a concentration-at-distance function (pure, with units).
- `tools/exposure` (population tract list), `tools/assessment` (scenario builder and receptor ranking), `tools/schemas.py`, `config/settings.toml` (reach of a scenario, how many receptors are listed).
- `api/schemas/workspace.py` and the projectors (contract regeneration), the Word report only if it lists stacks.
- `frontend`: `features/overview` (ribbon, Risk by group), `features/map` (inspector). Per the standing rule on dashboard panels, this change is explicitly requested by the user.
- Eval cassettes of the full-assessment scenarios must be re-recorded; the system prompt is not changed.
- Related but separate: `add-exposure-chain-visualizer` draws the pathway graph of a facility; it can read the scenario later and is not modified here.
