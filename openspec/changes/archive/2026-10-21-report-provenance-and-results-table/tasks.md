## 1. Chemical name

- [x] 1.1 Keep `preferredName` from the CAS-match entry on `Chemical` (optional; verify the field against a live response, with the detail endpoint as the fallback); tests for present, blank, non-string
- [x] 1.2 `ChemicalProperties.preferred_name` with source "CompTox" and a warning when absent; tool description says it is the only name to use; description and tool tests
- [x] 1.3 `Chemical.name` in the workspace contract, filled by the properties projector; export the contract and regenerate the frontend types; tests
- [x] 1.4 Chemical card shows the name before the CAS number, or the CAS number alone; test

## 2. Provenance in the report

- [x] 2.1 Prompt: "never invent" covers names and identifiers; the output format asks for each input's source as the result gives it; prompt tests
- [x] 2.2 Eval check `report_names_each_source` (tokens from the record's `source` strings; chemical named only as given); unit tests on hand-built records; added to the full-assessment scenario
- [x] 2.3 Spec: agent-evaluation deterministic check; agent-system-prompt requirements

## 3. Results table

- [x] 3.1 Pure helper: rows from `workspace.facilities` (outcome, tier, ranges, residents, status), default order and column sorts, assessed/folded split; Vitest tests
- [x] 3.2 `ResultsTable` component in the Overview panel: sortable headers, folded group with count, screened-out value in place of HQ, row activation frames and pins the facility, tabular numerals, horizontal scroll; tests
- [x] 3.3 Overview panel layout keeps the ribbon above the table and scrolls as one; fullscreen unchanged

## 4. Verification

- [x] 4.1 `uv run pytest`, ruff, pyright, bandit, function length (tracked and untracked files), `npm --prefix frontend run check`; all pass
- [x] 4.2 Live hexane run through the web API (2026-10-21, CompTox still down so no benchmarks and no name): the workspace carries all 1,231 facilities with an outcome (25 full, 475 worst case only, 731 not assessed beyond the refined cap); the report quotes the weather source ("Open-Meteo era5 reanalysis") and uses only the name the user gave; it did not name the residents' source (the new check would flag it). The table is verified by its tests; a headless screenshot could not be taken (Chrome attach failed)
- [x] 4.3 `uv run pytest -m eval` after the cassette was re-recorded (change `re-record-eval-cassette`): the new source check passed in every run whose details were kept
