## Context

See proposal.md. The draft (`tools/exposure/population.py`, uncommitted work by the user) is kept as the method: Census TIGERweb tracts (MapServer layer 8, "Census Tracts") that intersect a circle around the point (`distance` in meters, `AREALAND` per tract), grouped by state and county; for each county one ACS 5-year Data Profile request (`DP05_0001E` total, `DP05_0005E` under 5, `DP05_0019E` under 18, `DP05_0024E` 65 and over, `for=tract:*`); the counts of the intersecting tracts summed, scaled by circle area over total tract land area (at most 1), and turned into percent age bands. Default radius 1.609 km (one mile), radius floor 100 m, 30 s timeouts, ACS vintage 2023.

Checked live (2026-10-18):
- Layer 8 is "Census Tracts" with the fields the draft reads; the four variable codes are labelled total population, under 5 years, under 18 years and 65 years and over.
- **The Census Data API redirects every request without a key to `https://api.census.gov/data/missing_key.html`** (HTTP 302, empty body; also for other vintages and datasets). `httpx.get` does not follow redirects, so `raise_for_status()` raises and the draft's bare `except Exception` returns its screening default every time. The draft has therefore never returned census data in this environment.
- A point near Fall River, MA returns 17 tracts with 20.6 km2 of land against a circle of 8.13 km2 (scale 0.39); a point in the Gulf of Mexico returns no tract (the draft then reports 2,440 invented residents); a rural Nevada point returns one tract of 15,635 km2 (scale 0.0005).

Other departures from the project rules: no module docstring; a local `Population` type with `resolution_method` shadows `tools/schemas.Population` (which `calculate_exposure_metrics` uses); URLs, year, layer, variables and fallback hard-coded; one 101-line function; no input validation (radius unbounded, so a large radius means many county requests); no throttling or retries; `max(0.0, ...)` silently turns the ACS negative codes into zero; the fallback radius and the main radius are clamped differently; `ruff` F841 (`raw_18_64` unused); the old `test_metrics.py` still imports the tool from `metrics`.

## Goals / Non-Goals

**Goals:**
- Same inputs and method, in the project's layers, configuration-driven, validated, tested, with failures that are visible.
- Work with the Census key the service now requires, without ever putting the key in code, logs or results.
- A result type the exposure tool relies on, with provenance and warnings.

**Non-Goals:**
- Better spatial weighting (see the open question), margins of error, workers or visitors, or other countries.
- Block-level data, caching, or other age bands.
- Changing `calculate_exposure_metrics` beyond its documentation.

## Decisions

**D1. Layers.** `models/population.py`: `scale_to_circle(count, circle_area_m2, land_area_m2)` and `age_bands(total, under_5, under_18, over_65)`. `tools/exposure/helpers/census.py`: the HTTP side (tract query with truncation check, one ACS query per county, header-based column lookup, sentinel handling). `tools/exposure/helpers/receptors.py`: composition (validation, key, counts, model calls, warnings, default). `tools/exposure/population.py`: the `@tool` only wires settings, key and client. `config/population.py`: `PopulationSettings`.

**D2. The key.** `[population].api_key_env_var` (value `CENSUS_API_KEY`) names the variable; the key is read at the tool's edge (the same place the CompTox key is read, with `.env` loaded the same way), passed to the helper and sent as the `key` query parameter the service requires. It is never logged or returned: warnings name the variable, not its value. `.env.example` gains `CENSUS_API_KEY=your-census-key-here`. A missing or empty key means no ACS request and a warning.

**D3. Redirect = rejected key.** The shared client already treats any non-200, non-retryable status as final. `HttpRequestError` gains a `status_code` attribute (additive; existing callers unaffected) so the census helper can tell a 302 (or 400/401/403) from other failures and say "the Census API key is missing or was rejected" instead of a generic failure. Redirects are not followed.

**D4. ACS values.** Columns are located by name in the header row (not position). A cell is usable when it is a number that is not negative; null, text and the ACS negative codes (such as -666666666) make that tract unavailable and are counted, replacing the draft's silent `max(0, ...)`. Counts that are not nested make the whole answer unusable (D5 of the model spec).

**D5. Scaling is kept as in the draft, with its limits stated.** Counts are summed over the intersecting tracts and scaled once by circle area over total tract land area (capped at 1). That assumes people are spread evenly over the land of all intersecting tracts: it overcounts when the circle's edge clips a dense tract and undercounts the reverse, and it ignores that part of the circle may be water. It is a screening approximation; the description tells the LLM. Replacing it with per-tract intersection areas needs tract geometry and a polygon-intersection step (shapely or a numeric grid) and is the open question below.

**D6. Request bounds.** Radius within `[min, max]` (settings: 0.1 and 50 km), at most `max_counties` ACS requests (25: a 50 km circle around New York City reaches 19 counties and 4,100 tracts, one around Fall River, MA 11 counties), `exceededTransferLimit` from the tract service means an incomplete list (default, not a partial answer). Same throttle/retry policy fields as the other services, applied through `RetryingClient`.

**D7. Result and renames.** `Population` in `tools/schemas.py`: `total_population` (int), `age_distribution` (band -> percent), `source` (for example "Census ACS 2023 5-year (DP05), 14 tracts" or "screening default") and `warnings`. The draft's `resolution_method` becomes `source`, matching `Meteorology` and `StackParameters`. The local type in the tool module is removed.

**D8. Failure policy.** Data, network and key problems never raise: the tool returns the configured screening default with `source` "screening default" and a warning with the reason, as the meteorology and stack tools do. A bad configuration raises at load. "No tract found" (open water or outside the US) is treated as unknown, not as zero residents, because the two cannot be told apart from the tract service.

**D9. The screening default.** Kept from the draft as settings (300 residents per km2; age mix 5.7, 16.0, 60.9 and 17.4 percent). It is labelled and warned, but unsourced: task 0.2 compared the age mix with the national ACS 2023 5-year DP05 row (0-4 5.7, 5-17 16.5, 18-64 61.0, 65+ 16.8 percent; the draft's 16.0, 60.9 and 17.4 were close but not exact), so the verified row is used and cited; 300 residents per km2 has no source (the US average is about 36 per km2 and dense cities exceed 1,000) and stays a labelled suburban-scale assumption. The settings loader rejects age bands that do not sum to 100.

## Risks / Trade-offs

- [Open question: the weighting.] Uniform density over whole tracts is crude at a 1-mile radius, where tracts are small and density varies; a tract-geometry intersection would be better. Kept here to preserve the user's method; propose it as a follow-up change.
- [The user needs a Census key.] Free and instant by email at the Census Bureau; until it is set in `.env` the tool always returns the labelled default. Smoke tests are skipped without it.
- [TIGERweb limits.] The layer allows 100,000 records per query and did not truncate at 50 km around New York City; `exceededTransferLimit` is still checked.
- [The default can mislead.] 300 residents per km2 is far from rural or industrial reality. It is labelled and warned, and the agent is told to say so.
- [Margins of error.] ACS tract estimates carry sampling error that is ignored; small counts in a one-mile circle can be off by a wide margin. Stated in the description.
- [Vintage.] ACS 2023 is configured; a newer vintage is a one-line change but should be checked for variable-code changes (the labels are verified for 2023).
- [Request volume.] At most one tract request and `max_counties` ACS requests per call, no caching; acceptable for per-facility screening, worth caching if used in bulk.
