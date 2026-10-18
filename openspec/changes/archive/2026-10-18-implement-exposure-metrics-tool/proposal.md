## Why

`calculate_exposure_metrics` is the last stub (`raise NotImplementedError`) and the point of the whole assessment: every input it needs now exists (emission rate, stack candidates, meteorology, population, toxicity values), but nothing turns them into a concentration, a dose or a risk. The `models/` layer has the Gaussian plume, the dispersion coefficients, the dose and risk equations, but no plume rise and no wind-speed adjustment, so the effective release height cannot yet be computed. Its documented output (maximum concentration, dose, hazard quotient) also leaves the inhalation unit risk it already takes unused, and says nothing about which weather it assumes. The agent's system prompt was out of date for the same reason (it told the agent to call a tool that was removed) and, more basically, it listed tools and an order of calls, which cannot survive new tools or different questions.

## What Changes

- Implement `calculate_exposure_metrics` with the method of EPA's SCREEN3 screening model ("full meteorology" with the "automated distance array"), flat terrain, rural dispersion, ground-level receptor: for the given source, the maximum ground-level centerline concentration over EPA's 54 combinations of stability class and 10 m wind speed and SCREEN3's distance array from 100 m out to 10 km (the range in which the project's Briggs dispersion coefficients are valid; EPA's array continues to 50 km), with the distance and the weather that produced it.
- Report two scenarios: the **screening worst case** over that grid (headline), and the result for the **representative conditions** from `get_meteorological_boundary`, so the agent can show how far a typical year is from the worst case.
- Convert the 1-hour maximum to an annual average with EPA's screening factor before comparing it with chronic benchmarks; report both.
- Return the hazard quotient (concentration against the RfC) and the lifetime excess cancer risk (concentration against the IUR), each null with a warning when its toxicity value is missing, and the average daily dose per age band (0-4, 5-17, 18-64, 65+) for the bands present in the population, with the highest band named.
- Add the missing pure models: Briggs buoyant plume rise with stack-tip downwash, the wind-profile power law, the SCREEN-style search, and the inhalation exposure concentration and dose arithmetic (units in every docstring, `ValueError` on impossible input).
- Add an `[exposure]` settings table (meteorology grid, distance array, receptor height, annual factor, exposure factors, age-band inhalation rates and body weights) with a typed loader; every constant carries its source.
- Fail closed: no defaults and no invented numbers. Missing or impossible inputs give null results and warnings; setup errors raise.
- Extend `ExposureMetrics` and make `Toxicity` values optional (they can be null in `fetch_chemical_properties`); document the tool so the agent evaluates every stack candidate and reports the range.
- Make the agent system prompt teach how an exposure assessor reasons (evidence chain, evidence quality, conservatism, alternatives, disclosure) instead of listing tools and an order of calls, which breaks when tools change; the tool descriptions carry when to use each tool and how to read its results. A test fails if the prompt names a registered tool or numbers a list of steps. (The prompt itself was rewritten and tested ahead of this change; this change audits the tool descriptions against it.)

## Capabilities

### New Capabilities
- `exposure-metrics-tool`: the tool: inputs, outputs, scenarios, validation, null results with warnings.
- `screening-dispersion-model`: plume rise, wind profile and the SCREEN-style search over weather combinations and distances.
- `inhalation-risk-model`: exposure concentration, dose per age band, hazard quotient and cancer risk arithmetic.
- `agent-system-prompt`: the prompt teaches the assessment process, names no tool and prescribes no order; the tool descriptions carry the decisions.

### Modified Capabilities
- `app-configuration`: new `[exposure]` settings with validation.

## Impact

- Code: `tools/exposure/metrics.py` (thin tool), new `tools/exposure/helpers/assessment.py`, new `models/{plume_rise,wind_profile,screening,exposure}.py`, `config/exposure.py`, `config/settings.toml`, `tools/schemas.py` (`ExposureMetrics`, `Toxicity`), `prompts/agent_system.md`, README.
- Tests: `tests/models/`, `tests/tools/exposure/`, `tests/config/`, `tests/prompts/`.
- Dependencies: none new (numpy is already used).
- Method limits, stated in the tool description: flat terrain, no building downwash, no inversion lid or mixing-height limit, 10 m wind adjusted to stack height by a power law, final (not transitional) plume rise, a single source, no deposition or chemistry, and a screening maximum at a distance where people may not live.
