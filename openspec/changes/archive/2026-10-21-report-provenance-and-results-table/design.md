## Context

The report is written by the model from tool results; three gaps were observed in 13 scored
runs and one hexane run: an invented chemical name, a paraphrased weather source, and a table
cut short. Two are provenance the results already hold but the model drops; the third is a
list too long for the model to write.

## Decisions

- **Name from the CAS search, no extra request.** `_fetch_chemical` already reads the
  CAS-match entry; keep its `preferredName` on `Chemical` (optional) and surface it as
  `ChemicalProperties.preferred_name` with source "CompTox". Verify the field name against a
  live response first (the CTX `chemical/search/equal` entries are documented with
  `preferredName`, `dtxsid`, `casrn`); if absent, fall back to the detail endpoint already
  called for the molecular weight, which also carries it. Never fall back to any other source.
- **"Never invent" covers names.** One clause in the prompt's honesty rule plus one line in the
  properties description; measured the same way as the CAS rule (30 first replies) only if the
  prompt test alone proves insufficient.
- **Sources quoted, and checked in code.** The output format asks for the source text as the
  result gives it. A deterministic check `report_names_each_source` takes the distinctive token
  of each `source` string in the record (weather: the model name, e.g. "era5"; residents:
  "ACS"; properties: "CompTox" and each benchmark source) and the chemical name rule; it joins
  the full-assessment scenario. The judge keeps its criterion; the check makes the failure
  precise and stable.
- **Results table from the workspace, not the chat.** A `ResultsTable` feature component under
  `features/overview/`, fed by `workspace.facilities` and the status thresholds from the client
  config; sorting in a pure helper with Vitest tests; row activation calls the same framing and
  pin the map already exposes (through the workspace store, no cross-feature import). Grouping:
  assessed rows (`full`, `worst_case_only`, or a single-tool exposure) then a folded group for
  `screened_out_*` and facilities with no exposure. Digits and chips come from the client config.
- **Contract.** `Chemical.name: str | None` in `api/schemas/workspace.py`, exported to
  `schema.json` and `api.ts` with the existing scripts.

## Risks / Trade-offs

- A chemical CompTox cannot resolve has no name anywhere; the report must then stay with the
  CAS number, which reads drier but is honest.
- The source check keys on substrings of source strings; a source text change in a tool must
  update the token rule (kept in one place in `evals/checks.py`).
- The table repeats what the map card shows; accepted, it is the complete list in one view.
