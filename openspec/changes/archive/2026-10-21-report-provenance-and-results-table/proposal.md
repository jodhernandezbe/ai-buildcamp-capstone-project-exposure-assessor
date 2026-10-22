## Why

Thirteen scored eval runs on 2026-10-21 showed two ways the report departs from the evidence:
the model named CAS 96-12-8 differently in every run ("Acetoin", "Methacrolein",
"1,1,1-Trichloroacetone"; it is 1,2-dibromo-3-chloropropane) because the properties result
carries no name; and three of four judge failures were the weather source left unnamed ("actual
local weather") although the tool result says "Open-Meteo era5 reanalysis 2024". A hexane run
also showed the chat table stopping at a handful of the 157 facilities above the screening
thresholds; the map had every one, the report did not.

## What Changes

- `fetch_chemical_properties` returns the chemical's name (`preferred_name`, from CompTox's
  CAS search, which the lookup already makes), with its source; the workspace chemical card
  shows it. The prompt extends "never invent" from numbers to names and identifiers: a chemical
  is named only as a tool result names it, else by its CAS number alone.
- The report must name the source of every input as the results give it (`source` fields,
  benchmark sources, stack tier); the prompt says so in the output format, and a deterministic
  eval check verifies that each input's source string appears in the report, so the judge is
  no longer the only guard.
- The Overview panel gets a results table built from the workspace: one row per facility the
  workspace holds, with its screening outcome, stack tier, worst-case and representative HQ and
  cancer risk, residents and status, sortable, with the screened-out facilities folded below the
  assessed ones. It does not depend on the model's table; the chat can summarise.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `chemical-properties-tool`: returns the chemical's name and its source.
- `comptox-property-lookup`: the CAS search's preferred name is kept with the DTXSID.
- `agent-system-prompt`: names are never invented; every input's source is named in the report.
- `agent-evaluation`: a deterministic check that the report names each input's source.
- `assessment-dashboard-state`: the chemical carries its name.
- `web-ui-shell`: the chemical card shows the name; the Overview panel has a results table.

## Impact

- `tools/informatics/helpers/comptox.py`, `tools/informatics/properties.py`, `tools/schemas.py`
  (`ChemicalProperties.preferred_name`), the tool description and its tests.
- `prompts/agent_system.md` and its test; `evals/checks.py`, `evals/scenarios.py` and tests.
- `api/schemas/workspace.py` (`Chemical.name`), the properties projector, the contract export
  and `frontend/src/types`; `frontend/src/features/overview/` (chemical card, new
  `ResultsTable`), tests.
- Costs: one eval re-record once CompTox answers (the change `re-record-eval-cassette`).
