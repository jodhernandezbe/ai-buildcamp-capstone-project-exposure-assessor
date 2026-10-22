## Context

The inventory's `naics_code` comes from the TRI submission-NAICS join; the title came only from
`fetch_facility_industry` (two Envirofacts requests per record). The map draws the complete
inventory artifact, so untitled and unassessed facilities are visible as gaps.

## Goals / Non-Goals

- Goals: a title for every six-digit code without a request; every listed facility assessed
  unless the user narrows the scope; no change to the wire contract.
- Non-goals: titles for 2–5 digit codes (the Census six-digit lists do not hold them; the
  reference-table fallback still applies); storing the raw workbooks in git (`data/raw/` stays
  ignored); re-recording the eval cassettes.

## Decisions

- **One CSV, newest vintage wins.** `scripts/build_naics_titles.py` parses the Census workbooks
  with the standard library (zip + XML; no openpyxl) and writes `data/naics_titles.csv`
  (`naics_code,naics_title,vintage`), sorted and reproducible. Codes present in both lists take
  the 2022 title. Alternative rejected: a per-vintage lookup keyed by reporting year (TRI does
  not say which vintage a submission used).
- **Shared helper at `tools/emissions/helpers/naics_titles.py`.** Both the inventory and the
  industry tool need it, so it sits at the `helpers/` root (like `efservice.py`). The table is
  read once (`lru_cache` on the configured path and columns) and returned read-only
  (`MappingProxyType`); a missing file or column raises (setup error), bad rows are skipped.
- **Titles are attached in the tool, not the reducer.** `reduce.py` leaves `naics_title` null;
  `query_emissions_inventory` fills it from the table before ranking, so the reducer keeps no
  I/O or config reads.
- **Industry tool: local first.** `_title` returns the local title when the code is listed and
  asks `REF_NAICS` only otherwise; origin and warnings are unchanged.
- **Prompt, not code, for coverage.** The inventory already caps the list (`max_listed`), so
  "assess every facility the inventory lists" is bounded. The prompt still names no tool.

- **EIS IDs resolved for the listed facilities only.** The inventory can hold over a
  thousand facilities; the model sees at most `max_listed`. `rank_and_cap` takes an `enrich`
  step applied to the listed ones (one bulk request), and the complete list carries the
  enriched copies. The same-site match costs one request per facility without a registration
  plus one bulk request for its twins, so it is bounded by the listed count.
- **Same-site match is strict.** Exact FRS site name (the facility's own FRS name, not TRI's),
  same state, within `max_twin_distance_km`, and exactly one twin with EIS registrations. A
  looser match (name "contains") returned seven ADM sites in Decatur within a few km, so it
  would silently use another plant's stacks; it was rejected. Unmatched facilities keep an
  empty list and a note, and go to the SCC-based stack as before.
- **The NEI tool keeps its own lookup.** `eis_ids` is optional: given, no request is made;
  omitted (an older conversation, a hand-typed FRS ID), the FRS lookup runs as before.

- **Completion check in code, not wording alone.** Earlier evals (Oct 19) showed that wording
  does not reliably stop gpt-4.1 from truncating long tool sequences; a deferred reply is the
  same failure at the turn level. The reviewer is a small structured call on the request and
  the reply only (not the tool results), so it costs little; it runs only when the model ends
  without tool calls. The nudge is a `HumanMessage` named `completion_nudge`: provider-agnostic
  (a mid-conversation system message is not accepted everywhere), and filtered by name in the
  thread snapshot and the scope check's window. Rejected: a text heuristic ("I will now…") —
  fragile; a workspace-state check (facilities without exposure) — domain logic in `agent/`.

## Risks / Trade-offs

- A nudged turn costs a second agent pass; the limit (`max_nudges`, default 2) bounds it, and
  the reviewer errs toward "complete" when in doubt.

- Longer, costlier runs (up to 25 facilities × 3–4 calls). Mitigated by the inventory cap and
  the instruction to batch independent requests in one turn.
- The eval cassettes predate this prompt; they are recorded tool outputs, so they still replay,
  but the scored behaviour should be re-checked with `uv run pytest -m eval`.
