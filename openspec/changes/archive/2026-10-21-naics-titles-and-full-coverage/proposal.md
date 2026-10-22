## Why

Two gaps show on the map after a run. Most facilities carry a bare NAICS code with no industry
in words, because the title comes from a per-facility Envirofacts lookup the agent makes only
for the facilities it assesses. And most markers stay grey ("not computed"), because the prompt
asks the agent to keep the scope manageable and prioritise, so it assesses a few of the up to 25
facilities the inventory lists while the person sees every one of them.

## What Changes

- **Local NAICS titles**: the Census Bureau's six-digit NAICS code lists (2017 and 2022
  vintages) are merged into `data/naics_titles.csv` by a new build script, configured under
  `[industry]`. The emissions inventory gives every record a `naics_title` from that table, and
  the facility industry tool takes its title from the table first, asking TRI's reference table
  only for a code the lists do not have. The workspace shows the inventory's title for every
  facility until the industry tool answers.
- **Every listed facility is assessed**: the system prompt now tells the agent to assess every
  facility the inventory lists (the list is already the largest sources), to narrow the scope
  only when the user asks for particular facilities or a place, and to request the inputs of
  several facilities together in one turn. The inventory and industry tool descriptions follow
  suit (the inventory no longer says to decide which facilities to assess; the industry tool
  is for a null title only).

- **EIS IDs from the inventory, in bulk**: the inventory looks up the NEI (EIS) facility IDs
  of the facilities it lists in one request per hundred (the `dmapservice` list operator;
  Envirofacts `efservice` has none) and carries them as `eis_ids`; the NEI stack tool takes
  them and makes no lookup of its own. A facility whose TRI FRS ID has no EIS registration is
  matched to another FRS record of exactly the same site name in the same state within a short
  distance, and only when exactly one such record has EIS registrations (FRS holds some sites
  under several IDs); `eis_note` says what was done or why nothing could be.

- **Completion guardrail**: a live run showed the agent ending its turn after the inventory
  with "I will now gather stack, meteorology and population data…" and a self-chosen sample
  of five facilities, so no stack or exposure tool ever ran. An opt-in check after each
  reply (same pattern as the scope guardrail: the injected model reviews the reply against the
  user's request) sends such a reply back to work with a nudge, at most `max_nudges` times per
  turn; a reply waiting on the user (a CAS number, a choice) is left alone. The nudge is a
  named user-role message hidden from the interface and the scope check. The system prompt
  also says to do the work rather than announce it.

## Capabilities

### New Capabilities

- `completion-guardrail`: opt-in review of the agent's reply; a deferred reply is nudged back
  to work, bounded per turn, hidden from the interface; the check fails open.

### Modified Capabilities

- `emissions-inventory-tool`: the record carries `naics_title`; the description names every
  listed facility as a source to assess.
- `facility-industry-tool`: local code lists before the reference table; description says when
  it is still needed.
- `agent-system-prompt`: every listed facility is assessed; scope narrows only on request.
- `app-configuration`: `[industry]` names the titles table and its columns; `[frs_eis]`
  configures the bulk EIS lookup and the same-site match; `[ui.prompts]` names the completion
  prompts and the nudge limit.
- `stack-parameters-nei`: the tool accepts the inventory's `eis_ids` and then makes no request.

## Impact

- `config/settings.toml`, `config/industry.py`; `tools/emissions/helpers/naics_titles.py`
  (new, shared), `tools/emissions/inventory.py`, `tools/emissions/helpers/inventory/reduce.py`,
  `tools/emissions/helpers/industry/naics.py`, `tools/emissions/industry.py`, `tools/schemas.py`;
  `api/services/projectors/{payloads,facilities}.py`; `prompts/agent_system.md`;
  `scripts/build_naics_titles.py` (new); `data/naics_titles.csv` (new, 1151 codes).
- `config/frs_eis.py` (new), `tools/emissions/helpers/inventory/eis.py` (new),
  `tools/emissions/helpers/inventory/listing.py` (enrichment of the listed facilities),
  `tools/emissions/helpers/stack/nei_lookup.py`, `tools/emissions/stack.py`.
- The wire contract is unchanged (`Industry.naics_title` already existed).
- Runs take more tool calls and tokens: every listed facility is assessed. The recorded
  evaluation cassettes were not re-recorded in this change; `uv run pytest -m eval` should be
  re-run before relying on them.
