## Why

Every facility's annual release is turned into a g/s rate with one static assumption, 8,760
operating hours a year (`[emissions].operating_hours_per_year`). Census's plant capacity survey
shows most industries run far fewer hours (the committed baseline has 72 four-digit industries
from about 39 to 168 h/week), and the release is concentrated into those hours, so one number is
wrong for most facilities in both directions of interest. `data/census_qpc_baseline.parquet` now
holds average plant hours per week by NAICS code; the emissions inventory should use it.

## What Changes

- Add a per-industry operating-hours resolver: given a facility's primary NAICS code, find the
  baseline row by **longest prefix** (6, 5, 4, then 3 digits; the most specific code that has a
  row wins) and convert its h/week to h/year as `h/week x 365 / 7` (168 h/week gives exactly
  8,760).
- When no row matches (no NAICS code, a code shorter than three digits, or no baseline row for
  any of its prefixes), or the baseline cannot be used, fall back to the current configured
  8,760 h/yr. Nothing else about the fallback changes.
- Match efficiently: the baseline is read and validated once into a dict keyed by code; a lookup
  is at most four dict probes (no scan, no dataframe, no per-facility file read).
- Each emission record says where its hours came from (`operating_hours_source`: the QPC release
  and matched code with its h/week, or "default, no QPC match"), next to the existing
  `operating_hours_per_year`, and the API/workspace payload carries it.
- Put the baseline path, column names, prefix lengths and the days-per-year constant in a
  `[plant_hours]` section of `config/settings.toml` with a typed loader.
- Keep `[emissions].operating_hours_per_year` as the fallback and its validation unchanged.

## Capabilities

### New Capabilities
- `plant-operating-hours`: loading and validating the QPC baseline, longest-prefix match of a
  NAICS code, conversion from h/week to h/year, fallback, and the configuration that drives them.

### Modified Capabilities
- `emissions-inventory-tool`: the emission rate uses the facility's own operating hours (QPC
  match, else the configured default) and each record states the source of its hours.

## Impact

- Code: `config/plant_hours.py` (new) and `config/settings.toml`; `commons/prefix.py` (generic
  longest-prefix lookup); `tools/emissions/helpers/inventory/` (`plant_hours.py` new; `rate.py`,
  `reduce.py`, `lookup.py` take an injected resolver); `tools/emissions/inventory.py` builds it at
  the edge; `tools/schemas.py`, `api/schemas/workspace.py`, `api/services/projectors/*`, the
  exported API contract and frontend types gain one string field.
- Behavior: emission rates (g/s) of facilities with a match rise by 8,760 / hours-per-year, so
  downstream exposure and risk numbers change for them; facilities without a match are unchanged.
- Data: reads `data/census_qpc_baseline.parquet` (already committed); no new dependency.
- Evals: tool outputs and numbers change, so the full-assessment cassette and the evals are
  re-run, and re-recorded if replay no longer matches.
- Out of scope: changing the baseline (it currently holds only four-digit codes, see design),
  showing the source in the UI, and how exposure time is applied to the operating-hours rate.
