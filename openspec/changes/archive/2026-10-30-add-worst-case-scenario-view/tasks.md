## 1. Model functions

- [x] 1.1 Add great-circle distance and bearing (units in the docstring, input validation) to the population model, with tests for due east, same point and invalid coordinates
- [x] 1.2 Add concentration at a stated distance for a fixed scenario to the dispersion model; test that it equals the maximum at the maximum's distance, never exceeds it elsewhere, and rejects invalid input

## 2. Population tracts

- [x] 2.1 Add the tract internal-point fields to `[population]` configuration and parse them (signed strings) into `Tract`; a tract without a usable point is counted but not listed, with a warning
- [x] 2.2 Return the tract list (residents, age mix, distance m, bearing deg) from the population tool, capped by configuration with a count of those left out; pooled result unchanged; update `tools/schemas.py` and the tool description
- [x] 2.3 Tests for the list, the cap, a missing point, the screening default, and a live smoke test on a Puerto Rico facility

## 3. Scenario builder

- [x] 3.1 Add `[scenario]` configuration (receptor fraction, receptor cap, pathway names and factor labels) with a typed loader
- [x] 3.2 Define the generic scenario types (pathway, quantity, tier, factors with group/value/unit/source or reason, receptors) in `tools/schemas.py` and a `PATHWAYS` registry in `tools/assessment/helpers/scenarios/`
- [x] 3.3 Community inhalation entry: factors from the stack results (`high_stack`, release, conditions); receptors ranked with the model function, "no resident where the maximum falls" with the nearest tract, and the count of tracts outside the model range
- [x] 3.4 Build the worker scenario from the worst-case ventilation tier already carried by the occupational result (airflow, mixing factor, schedule, limit), with the workers as receptors
- [x] 3.5 Choose the driver per pathway and quantity among assessed facilities; worst-case-only facilities get a scenario without receptors; add the scenarios and drivers to the assessment artifact and one line per driver to the text the model reads
- [x] 3.6 Tests per rule: stack choice, no cancer risk, nobody at the maximum, drivers differing by quantity, no extra requests, no wording of a regulatory finding, and a test pathway registered in the test that reaches the output unchanged

## 4. API contract

- [x] 4.1 Add the scenario, receptor and driver models to `api/schemas/workspace.py`; validate them separately in the projectors so an invalid one is left out with a warning
- [x] 4.2 Project the scenarios and the drivers into `WorkspaceState`; regenerate the contract and types; default them in the store for an older server
- [x] 4.3 Backend tests under `tests/api/`, including an invalid scenario and an older payload

## 5. Frontend

- [x] 5.1 A generic scenario card (pathway, value and tier, facility, factors by group, receptors or the reason) used by the ribbon for each driver, with a closed "Other facilities" disclosure; no pathway-specific code
- [x] 5.2 Inspector: scenarios first, the driving stack marked, receptors with age bands, distance and bearing; other stacks in a closed section
- [x] 5.3 Risk by group: tooltips name the facility and stack that drive a bar
- [x] 5.4 Map: mark the driving facility of the selected result and draw the receptors of the selected driver at their bearing and distance
- [x] 5.5 Component and helper tests for each of the above, including "not reported" with a reason and the nobody-there case

## 6. Evals, specs and gates

- [x] 6.1 Re-record the full-assessment scenarios; run the evals three times and fix any unrecorded call with an `ExtraCall`
- [x] 6.2 Run ruff, pyright, bandit, function length, pytest, the frontend check and build, `pre-commit run --all-files` and `openspec validate --strict`
