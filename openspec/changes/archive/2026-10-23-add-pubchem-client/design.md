## Context

See proposal.md. Current state:

- `fetch_chemical_properties` (`tools/informatics/properties.py`) builds a `_Collected` from
  `ComptoxLookup` results and converts/validates each field (`_add_one`, `_convert_checked`,
  Pint with aliases from `[units.aliases]`). Missing fields are None with a warning. Default
  collaborators come from `_services()`.
- `tools/http.py` `RetryingClient` throttles, retries and times out; `read_across/pubchem.py`
  uses it for a different PubChem call and stays as it is.
- Rules: config for URLs/headings/units; helpers in `tools/informatics/helpers/`; no untyped
  `dict`; functions at most 18 lines; failures are None plus a reason; tools do not import other
  tool folders; `commons/` does no I/O.

## Goals / Non-Goals

**Goals:** a second, conservative source for the configured fields, inside the existing tool,
with the same validation and clear provenance; a reusable client (CAS/SMILES/name → CID →
record) for the next step.

**Non-Goals:** a new agent tool; hazard (GHS) or LC50/LD50 parsing; PubChem names; any
toxicity value from PubChem; changing CompTox behavior; async I/O.

## Decisions

**A fallback step after CompTox, not a merge.** `lookup_chemical_properties` stays as is for
CompTox. A new step, `complete_from_pubchem(out, cas, pubchem, settings, aliases)`, runs
afterwards, computes the configured fields still None in `_Collected.values`, returns early if
none, and otherwise asks a `PubchemLookup` for candidates and feeds each through the existing
`_add_one` (so conversion, positivity and the "rejected value" warnings are the same code).
Alternative: query both sources and compare; rejected: twice the requests, and the question
is only "is there anything".

**Dependency injection.** `lookup_chemical_properties` gains an optional `pubchem:
PubchemLookup | None = None` and `pubchem_settings`; `None` means no fallback (existing tests
and callers keep working). `_services()` builds the default `PubchemLookup` at the outer edge.
`PubchemLookup` is a Protocol-like small class: `candidates(cas, fields) -> PubchemResult`
returning, per field, a reported value `(value, unit)` or a reason.

**Field-driven configuration.** `[[pubchem.fields]]` entries: `key` (the result field),
`heading` (path under the PUG View record), `target_unit` (kept next to CompTox's for the same
key; one is canonical, a test asserts they match), optional `temperature_range_c`, optional
`structured_unit`. Initial entries: `molecular_weight` ("Computed Properties" → "Molecular
Weight", structured `g/mol`), `vapor_pressure` ("Experimental Properties" → "Vapor Pressure",
temperature 20–25 °C), `density` ("Experimental Properties" → "Density"). No `rfd`, `rfc`, `sf`
or `iur` entries; the parser has no special case for any field, so one entry is enough to add
one later. Adding unit spellings PubChem uses (`g/cu cm`, `mm Hg`, ...) goes in
`[units.aliases]`.

**Confirm the match by CAS.** Name search with a CAS number can hit a synonym of another
chemical. The record's "Names and Identifiers" → "Other Identifiers" → "CAS" strings (heading
path in config) must contain the requested CAS (after `format_cas` normalization of each
string). Otherwise reject and warn. Only for CAS searches.

**One request pair per chemical.** CID search, then one PUG View fetch carrying molecular
weight, vapor pressure, density and CAS. No separate PUG REST property call. Both are cached.

**Statement reading (`statements.py`).** Candidates per field are the `Information` items under
the heading. Prefer `Value.Number` + `Value.Unit`; else the string from
`Value.StringWithMarkup[*].String`, matched by one regex `^\s*(number)\s*(unit)(?:\s+at\s+(number)\s*°?\s*C)?` with
fullmatch-style strictness: exactly one number, one unit token, optional temperature; anything
with `-`, `<`, `>`, `~`, `about`, or two numbers is skipped. Temperature out of the configured
range is skipped. Each skip carries a reason; the unit must convert via Pint, and this is
checked by the existing `_convert_checked`, but pre-converted per candidate so agreement is
compared in target units. Several candidates: median if max/min ≤ `agreement_ratio` (config,
default 2.0 for vapor pressure and density), else none with "statements conflict". Numeric
values never come from `bool` or a non-finite number.

**Client modules** (`tools/informatics/helpers/pubchem/`): `identifiers.py` (CAS → SMILES →
name detection, RDKit canonicalization with logging blocked, URL encoding), `client.py`
(`get_cid_by_identifier`, `fetch_pubchem_pug_view_json`, CAS confirmation, `Lookup[T]` value-
plus-reason dataclass), `cache.py` (SQLite), `sections.py` (heading traversal), `statements.py`,
`resolve.py` (`resolve_compound_data`: kind → CID → record → confirmation; returns kind, SMILES
used, CID, record and warnings, no parsing), and `lookup.py` (`PubchemLookup`, the tool-facing
facade). `get_cid_by_identifier(query, search_type="smiles")` keeps the requested signature and
returns `Lookup[int]`; `.value` is the `int | None`.

**Cache and rate limit** as in the request-policy spec: stdlib `sqlite3`, parameterized queries,
`.cache/pubchem/responses.sqlite`, TTL from config, success and 404 cached, failures not,
every cache error fail-soft with a warning; delay 0.25 s, rejected below 0.2 s. The cache layer
is a `CachedJsonClient` with the same `get_json` as `RetryingClient`.

**Provenance, and no change to the tool description.** `sources[field] = "PubChem"` plus a
warning such as `density: CompTox had no value; taken from PubChem (median of 2 statements)`.
`ChemicalProperties.sources` comments are updated. The agent-visible description of
`fetch_chemical_properties` is **not** changed: measured with the full-assessment eval
(CAS 96-12-8, `gpt-4.1`, whole file of 10 checks per run), the unchanged description passed
13 of 13 runs (5 baseline + 8 with this code); a PubChem paragraph in it passed 4 of 11,
a shorter paragraph 2 of 8, and mentioning `"PubChem"` only in the `sources` line 4 of 8, the
failures being the batch-versus-chain route choice (an unrecorded `assess_facilities` call)
and a thinner report. The output already tells the model where each value came from, so the
description stays as it was (see the project note on fragile wording).

**Tests.** Mock `httpx` via `MockTransport`; no network. Fixtures keep the real PUG View
shape with placeholder numbers, never real-looking measurements. Negative test per rule:
unconfirmed CAS, ambiguous CID, range, inequality, dimensionless density, wrong temperature,
conflicting statements, bool/NaN/negative, unreachable PubChem, corrupt cache. Properties tests
assert PubChem is not called when nothing is missing, never overwrites CompTox, and never fills
`preferred_name` or toxicity. A live smoke test (butane) is excluded from the default run.

## Risks / Trade-offs

- [PubChem free text is messy] → only single number + unit statements, temperature window,
  agreement check; otherwise None, as before the change.
- [Wrong chemical matched by a name search] → CAS confirmation from the record itself.
- [PubChem value looks as trustworthy as CompTox's to the model] → source "PubChem" and a
  warning on each use in the result; the description is untouched because changing it made the
  evaluation unstable.
- [Extra latency (two requests plus a large record) on gaps] → only when a field is missing;
  cached; 0.25 s delay.
- [Layout change in PUG View] → headings in config, missing parts give a warning, smoke test.
- [Vapor pressure and density at unstated or different temperatures] → temperature window;
  statements with no temperature are accepted for density and molecular weight only if config
  says `allow_missing_temperature` (true for density, false for vapor pressure).
- [Use of PubChem when CompTox does not know the CAS] → allowed but guarded by CAS confirmation;
  name and toxicity stay None.

## Migration Plan

Additive and default-on for the tool, no new setting needed. Callers that pass no PubChem
collaborator behave as before. Rollback: revert the commit; delete the cache file at will.
