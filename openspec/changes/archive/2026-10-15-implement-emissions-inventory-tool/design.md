## Context

See proposal.md for motivation. Current state: `tools/emissions/inventory.py` is a stub returning nothing; `EmissionRecord` holds `frs_id`, `facility_name`, `emission_rate` (g/s). CompTox helpers under `tools/informatics/helpers/` and `config/loader.py` show the pattern to follow (injected HTTP client and `sleep`, settings from `settings.toml`, `None`/empty plus warning for data problems, setup errors raise).

Findings from probing the live API (2026-10-15) and the sample in `sample.json`:

- The joined URL `.../tri_release_qty/cas_registry_number/50-00-0/rows/1:5/JSON` answers in ~0.6 s, ~5 KB per row (the join is very wide: ~180 columns, most irrelevant). Each TRI form yields one row per environmental medium (AIR STACK, LANDF8795, LAND TREA, OTH DISP, ...), and rows come back in ascending year (1988 first), so the latest years are at the end.
- `COUNT` on the joined view timed out at 40 s, so total size cannot be known up front.
- Spike results (formaldehyde, 50-00-0): `.../cas_registry_number/50-00-0/environmental_medium/AIR%20STACK/rows/a:b/JSON` (no `/equals/`) filters server-side; all 5,000 rows fetched were AIR STACK. The `/equals/` form returned zero rows. Pages of 100 / 500 / 1000 rows took ~10 / ~10.5 / ~12.6 s (0.5 / 2.6 / 5.3 MB), so a fixed cost of ~5-10 s per request dominates and bigger pages are cheaper per row. More than 5,000 AIR STACK rows exist for this chemical; rows are not ordered by year, so there is no early stop. An out-of-range page timed out at 90 s instead of returning an empty list, so the end must be detected by a short page, never by probing past the end.
- On real rows: `epa_registry_id` was always set and `frs_id` always null; `reporting_year` is a string; `total_release` is int, float or null (~20% null, `0` also occurs); ~14% of rows have null `pref_*` coordinates; ~1% of facility-years have two forms with different quantities (e.g. 909 and 2683 lb, same facility and year, no revision code); `pref_longitude` is positive for NY, NC, MA, PR and VI (west sign dropped).
- Old rows have `frs_id: null` but a populated `epa_registry_id` (the 12-digit FRS registry ID); location is in `pref_latitude`/`pref_longitude` (decimal degrees) while `fac_latitude`/`fac_longitude` are packed DDMMSS integers (`181500` = 18°15'00"). `pref_longitude` was `66.125` for a Puerto Rico facility, i.e. the west sign is dropped.
- `total_release` is `null` when `release_na = "1"`; `unit_of_measure` is `"Pounds"` (annual quantity).
- The reference extractor (`ChemSoRGNN/.../tri_files.py`) uses 5 concurrent requests, a 0.1 s delay, treats 404 as end-of-data, stops on a short page, and has no retry or `429` handling; it also has a hard-coded `end > 10` cap that makes it only fetch a handful of rows, so it is a source of ideas, not of code.

## Goals / Non-Goals

**Goals:**
- Return the latest-year AIR STACK record per facility for a CAS, with identity, location, quantity and unit.
- Be polite to Envirofacts and robust to throttling and timeouts without unbounded memory or time.
- Keep media, paging and timing in `settings.toml`; adding a medium is a config edit.

**Non-Goals:**
- Facility- or sector-specific operating hours (the helper is the extension point; only the constant is built now), stack parameters, or facility metadata beyond what TRI rows carry (later tools).
- Fugitive, water, land or off-site media (config-ready, but not enabled or tested beyond one extra-medium unit test).
- A persistent cache or a bulk download of TRI (revisit if per-CAS latency hurts).
- Concurrent fetching.

## Decisions

**1. Chunked, sequential paging over one big request.** One request for everything is the fewest queries but (a) the join is slow (the COUNT timed out), so a big range risks hitting the timeout and losing everything, (b) at ~5 KB/row a popular chemical such as formaldehyde could be tens of thousands of rows, hundreds of MB in one response, and (c) a single failure restarts all work. Pages of a configured size (default 1000 rows, ~5 MB, ~11 s, chosen because per-request overhead dominates) bound each request, allow retry of just the failed page, and let us reduce rows as they stream. Cost: more requests, offset by the small per-page delay. Alternative considered: 5 concurrent workers as in the reference code. Rejected: offset paging order matters for early stop, and sequential access is the safest default for a public shared API; concurrency can be added behind a config value later if latency demands it.

**2. Reduce while streaming.** Each page is filtered to configured media, validated, and folded into a dict keyed by `(environmental_medium, facility_id)` keeping the greater `reporting_year`. Memory is O(facilities), not O(rows). Several reports in the same latest year (~1% of facility-years) are summed, because they are separate forms with different quantities and no revision marker, and under-counting a source is the less conservative error; the combined count is warned. Facility location is tracked separately from the quantity: it is the coordinates of the facility's most recent row that has valid ones, since the latest row often lacks them.

**3. Latest year wins, then validate.** Dedup picks the latest year first; only then is the quantity validated. If the latest record has no usable quantity the facility is omitted (counted in a warning) instead of silently falling back to a stale year, since an older year would overstate a source that has since reported no release. This keeps "latest available year" meaning exactly what the user asked.

**4. Facility key.** `epa_registry_id` is the FRS ID (confirmed by the user; the TRI `frs_id` column is empty in older rows such as the sample). Use `epa_registry_id`, falling back to `frs_id`; both field names are configuration. Rows with neither are skipped with a warning. The returned `frs_id` is the resolved value so downstream tools (`get_facility_metadata`, `fetch_stack_parameters`) receive a usable ID.

**5. Location: `pref_*` columns, signed.** Use `pref_latitude`/`pref_longitude` (decimal degrees) and ignore the packed `fac_*` columns. Because the sign of longitude is dropped, negate it for states not listed in a configured `east_longitude_states` (`GU`, `MP`), otherwise keep it. Out-of-range values are discarded rather than corrected. The spike verifies this assumption against several states before it is trusted; if TRI turns out to be inconsistent, the fallback is to drop the sign logic and keep coordinates as reported with a warning.

**6. Keep the reported value, add a converted rate.** The record carries `total_release` and `unit` exactly as reported, plus `emission_rate` (g/s). The rate is `convert(total_release, unit, "kg", aliases)` from `commons/units.py` (a `Pounds` alias is added to `[units.aliases]`) passed to the existing `models.risk.calculate_emission_rate(annual_mass_kg, operating_hours_per_year)` (one source of truth for the equation; the hours are always passed explicitly from config, never left to that function's default). `UnitConversionError` discards the row with a counted warning (fail closed). Keeping the reported pair means the conversion can be audited and redone with better hours later.

**6b. Operating hours behind one helper, value in config.** `[emissions] operating_hours_per_year = 8760` in `settings.toml` (conservative: continuous operation, which maximizes the average rate) is loaded into a frozen settings dataclass and validated (finite, > 0, <= 8784, not a bool). `tools/emissions/helpers/rate.py` holds `operating_hours_per_year(settings)`, the only place that decides the hours; today it returns the configured value, and later it can take facility context (NAICS, SCC, reported days) without touching callers. The pure `to_emission_rate(value, unit, hours, aliases)` takes the hours as an argument. No numeric literal for the hours exists in Python. Alternative considered: a module constant in `rate.py`; rejected because the project rule is that tunables live in `config/`.

**7. Rate-limit handling.** Settings: `page_size`, `delay_seconds` between every request, `timeout_seconds`, `max_retries`, `backoff_seconds` (doubling), `max_pages`. HTTP 429 and 5xx/timeouts are retried, honouring `Retry-After`; other 4xx and malformed bodies are non-retryable failures. A 404 with an empty body is treated as end-of-data (observed in the reference code) only after the spike confirms Envirofacts behaves that way. Exhausted retries fail the whole lookup (empty list + warning) rather than returning a partial list that looks complete. Hitting `max_pages` returns what was gathered and warns that it may be incomplete.

**8. Structure.** `tools/emissions/helpers/tri.py` (HTTP paging, injected client and `sleep`) and `tools/emissions/helpers/reduce.py` (row validation and dedup, pure), `tools/emissions/helpers/rate.py` (operating-hours helper and pound-to-g/s conversion, pure), with `inventory.py` composing them and building default collaborators at the edge. Helpers stay in `tools/emissions/` and do not import other tool folders. CAS validation (`format_cas`) moved from `tools/informatics/helpers/` to `commons/cas.py` so both tool groups share it without importing each other. Config: `TriSettings` frozen dataclass in `config/loader.py`.

**9. Reporting problems.** The tool returns `list[EmissionRecord]` (the registered tool signature stays simple); data problems are logged as counted warnings. If the LLM needs the warnings, a wrapper TypedDict can follow in a later change.

## Risks / Trade-offs

- [Large chemicals take minutes: ~11 s per 1000-row page, and formaldehyde AIR STACK alone exceeds 5 pages] -> `max_pages` (default 40, ~7 min worst case) bounds it and warns when hit; a per-process cache keyed by CAS is a follow-up.
- [A result with an exact multiple of the page size makes the tool request a page past the end, which timed out in the spike] -> Accepted (rare, about 1 in the page size); it fails closed with a warning rather than returning a possibly short list.
- [Envirofacts has undocumented limits] -> Retry/backoff plus delay; defaults chosen conservatively and tuned from the spike's measurements.
- [Sign guess for longitude] -> Validated in the spike; out-of-range coordinates are discarded; the east-hemisphere list is config.
- [Offset paging drifts if data changes mid-run] -> Acceptable for a screening tool; TRI updates annually.
- [8,760 h/yr averages the release over a full year] -> It is conservative for long-term average exposure but understates peak rates of intermittent sources; the hours are reported on each record and configurable, and the helper is the planned extension point.
- [BREAKING stub change] -> Nothing consumes the stub yet; registry test and docstring updated in the same change.

## Open Questions

- Whether to add an in-memory cache later.
- Whether summing same-year duplicate reports matches how TRI users treat them (chosen as the conservative default).
