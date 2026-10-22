## Context

Today `Reducer.records()` (`tools/emissions/helpers/inventory/reduce.py`) calls
`operating_hours_per_year(emissions)` once and uses that single number for every facility slot:
`to_emission_rate(quantity, unit, hours)` -> g/s, and `hours` is copied into each
`EmissionRecord`. The facility's primary NAICS code (`slot.naics_code`, a string of 2-6 digits or
None) is already on the slot when the rate is computed. `rate.py` says this function is "the one
place that decides the hours", so the seam exists.

The baseline `data/census_qpc_baseline.parquet` (built by `scripts.build_census_qpc_baseline`)
has columns `naics_code`, `avg_plant_hours_per_week`, `source_naics`, `source_title`,
`release_year`, `release_quarter`, and release metadata (`qpc.release` etc.).

**A fact to confirm.** The request says the parquet has 3-, 4-, 5- and 6-digit codes. The
committed file has **72 rows, all four-digit codes**: that was the rule chosen when it was built
(a four-digit code gets a value only when one published row covers it entirely), and 5/6-digit
QPC rows (refineries 32411, petrochemicals 32511, plastics resin 325211, ...) were skipped. So
today a refinery (324110) finds no 3241 row and gets the 8,760 default. The matcher below is
written for codes of any length 3-6, so if the baseline is later rebuilt with finer rows, matching
improves with no code change. Rebuilding the baseline is out of scope here.

## Goals / Non-Goals

**Goals:** per-facility operating hours from the baseline by most-specific NAICS match; exact
current behavior as the fallback; cheap lookups; visible provenance of the hours.

**Non-Goals:** changing the baseline's content; UI display of the source; revisiting how exposure
time is applied (see Risks); seasonal or per-unit operating schedules.

## Decisions

1. **Matching algorithm: probe prefixes, longest first, in a dict.**
   Build once `Mapping[str, float]` (code -> h/week). For a facility code `c` try
   `c[:n]` for `n = len(c)` down to `min_digits` (3) and return the first hit.
   At most 4 probes for a 6-digit code, O(1) memory per lookup, and "specific beats general"
   is the loop order. It only ever looks at prefixes of the facility's code, so a 4-digit
   facility code cannot match a 5-digit baseline row (that row describes a sub-industry, not the
   whole). Rejected: a trie (more code, no gain with at most 4 levels); sorted array + `bisect`
   (O(log n) and fiddly prefix handling); scanning with `startswith` (O(n) per facility);
   `pandas` merge (not a dependency, per-call overhead, harder to test); a SQL/`LIKE` query.
   The generic part lives in `commons/prefix.py`:
   `longest_prefix(table: Mapping[str, V], key: str, *, min_length: int) -> tuple[str, V] | None`
   (pure, no project knowledge, typed generic), with its own negative tests.

2. **Loading the baseline (`tools/emissions/helpers/inventory/plant_hours.py`).**
   `load_baseline(settings) -> Baseline` where `Baseline` is a frozen dataclass of
   `hours_per_week: Mapping[str, float]` (read-only `MappingProxyType`), `release: str` (from the
   parquet metadata `qpc.release`), and `warnings: tuple[str, ...]`. Reads only the two configured
   columns with `pyarrow.parquet.read_table(columns=...)`; pyarrow is untyped, so it stays inside
   this one module behind casts (like `scripts/qpc/output.py`). Each row is validated: code is an
   ASCII digit string of `min_digits..max_digits`, hours finite, not bool, `0 < h <= max_hours`;
   duplicates drop all copies of that code. Bad rows are counted into one warning
   ("ignored N baseline rows"). A missing/unreadable file, missing column or missing release
   metadata yields an empty `Baseline` with a single warning (data problem -> fallback, not an
   exception); a malformed `[plant_hours]` section raises at config load (setup error). The
   loader is `lru_cache`d on the settings object, so the file is read once per process; callers get
   immutable data (no copies needed).

3. **Resolver and conversion.** In the same module:
   `class PlantHours` (constructed with a `Baseline`, `PlantHoursSettings`, and the default hours)
   exposes `__call__(naics_code: str | None) -> OperatingHours`, where `OperatingHours` is a frozen
   dataclass `(hours_per_year: float, source: str)`. Steps: normalize the code with
   `tools.digits.digit_string` (2-6 digits, else no match), `longest_prefix`, then
   `hours_per_year = hours_per_week * days_per_year / 7` (365/7 so 168 -> 8,760 exactly). The
   result is checked `0 < h <= 8760`. Fallback returns the configured default with a reason.
   Source strings, e.g. `Census QPC 2026Q2, NAICS 3252: 111.7 plant hours/week` and
   `default 8760 h/yr (no QPC match for 324110)`, `default 8760 h/yr (no NAICS code)`,
   `default 8760 h/yr (QPC baseline unavailable)`. A per-code `functools.lru_cache` is not needed:
   a lookup is a handful of dict probes.

4. **Wiring (dependency inversion).** `rate.py::operating_hours_per_year(settings)` stays as the
   default provider. `Reducer.records(emissions, aliases, locate, hours_for=None)` takes an
   optional `HoursFor = Callable[[str | None], OperatingHours]`; `None` means the old behavior
   with source "default". `_record` computes `hours = hours_for(slot.naics_code)` per slot and
   passes `hours.hours_per_year` to `to_emission_rate` and both values into `_reported`.
   `lookup_emissions(..., hours_for=...)` forwards it, and `tools/emissions/inventory.py` (the
   edge, where `get_emissions_settings()` is already read) builds `PlantHours` from
   `get_plant_hours_settings()` and passes it. The baseline warning, if any, is appended to the
   inventory's existing warnings list. Tests inject a fake resolver; the reducer never imports
   pyarrow or the settings.

5. **Record schema and API.** `EmissionRecord` (`tools/schemas.py`) gains
   `operating_hours_source: str` next to `operating_hours_per_year`. The API workspace schema and
   projectors (`api/schemas/workspace.py`, `api/services/projectors/payloads.py`, `facilities.py`)
   pass it through; `scripts/export_contract.py` is re-run so the committed contract and
   `frontend` types stay in sync (`npm --prefix frontend run check`). No UI change.
   Existing callers that build `EmissionRecord`s in tests get the field via a helper default.

6. **Config.** `[plant_hours]` in `config/settings.toml` + `config/plant_hours.py`
   (`PlantHoursSettings`, `load_plant_hours_settings`, cached `get_plant_hours_settings`, validators
   from `config/parsing.py`): `baseline_path = "data/census_qpc_baseline.parquet"`,
   `code_column = "naics_code"`, `hours_column = "avg_plant_hours_per_week"`, `min_digits = 3`,
   `max_digits = 6`, `days_per_year = 365`, `max_hours_per_week = 168`. `min_digits <= max_digits`,
   `days_per_year` positive finite. These duplicate no value of `[qpc]` on purpose: `[qpc]`
   configures building the file, `[plant_hours]` configures reading it (different reasons to
   change). `[emissions].operating_hours_per_year` is untouched.

7. **Prompt/tool text.** The `fetch_emissions` tool docstring says hours now come from the
   industry baseline when matched and states how to read `operating_hours_source`. The system
   prompt is not changed unless the provenance eval requires the report to name this source
   (see tasks 5.x); per project memory, the prompt teaches reasoning, not tool order.

## Risks / Trade-offs

- **Numbers move.** A facility at 84 h/week gets a 2x emission rate in g/s. That is the intent
  (the same annual mass emitted in fewer hours), but every downstream exposure/risk value for
  matched facilities changes and eval expectations may shift. Called out in the proposal.
- **Exposure time interplay (not decided here).** The rate is now "g/s while operating" while the
  exposure model still assumes a receptor exposure time of 24 h/day (`[exposure]`). For a
  long-term average concentration this overstates exposure by about `8760 / hours`. Whether to
  scale the exposure time or accept it as a conservative screening choice is a separate decision
  for the owner; this change does not touch it.
- **Coarse coverage today.** With only four-digit rows, the heavy-emitting 5/6-digit industries
  fall back to 8,760 (conservative on the annual-average side). The source string makes this
  visible per facility.
- **Group values.** A baseline row for `3111,7,8` gives the same hours to three industries; the
  source string reports the matched baseline code, and the parquet's `source_naics` keeps the group.
- **Staleness.** The baseline is a committed snapshot; its release is shown in every source
  string so an old file is visible. No automatic age check.
- **Silent degradation.** A broken baseline falls back with one warning instead of failing the
  inventory, matching "no match -> fallback"; the warning keeps it visible.

## Open Questions

- Rebuild the baseline with 5/6-digit rows (a different rule in `scripts.qpc`)? Not needed for
  this change to be correct, but it decides how many facilities it helps.
- Exposure-time interplay above: scale or keep as is?
