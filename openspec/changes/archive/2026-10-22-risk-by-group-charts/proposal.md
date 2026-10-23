## Why

The map shows every facility and the summary ribbon shows the single worst case. Neither says
*where the risk sits*: which industries, which TSCA conditions of use, which life cycle stages
carry the highest hazard quotient and cancer risk, and how many facilities that rests on. With
conditions of use and life cycle stages now on every facility, the dashboard can answer that, and
because HQ and cancer risk are dimensionless the groups can be compared on one chart.

## What Changes

- Add three bar charts to the Overview panel, between the summary ribbon and the results table,
  one per grouping: **industry (NAICS 3-digit subsector)**, **condition of use** and **TSCA life
  cycle stage**. Each shows the **top 5 groups**, with the x-axis the group and **two bars per
  group**: the highest worst-case **hazard quotient** (non-cancer) and the highest worst-case
  **lifetime cancer risk**, both unitless, on a logarithmic axis with the configured thresholds
  of concern drawn as reference lines.
- A group's value is the **highest** worst-case value among its fully assessed facilities (a
  selection of values the API already sent; nothing is summed or averaged in the browser). Hover
  shows, per bar, the value, the facility it comes from, that facility's worst-case concentration
  (the exposure quantity, µg/m³), and the **number of facilities** in the group (how many were
  assessed).
- Groups are ranked by hazard quotient or, with a small switch on the chart, by cancer risk.
- Each new chart section can **expand** to fill the panel (and restore), so the space is used
  where the user is looking. The existing cards, results table and map are unchanged.
- Give every facility its **3-digit NAICS subsector** (code and title) so the industry grouping
  has words to show: titles come from Census's official 2-6 digit NAICS 2022 workbook (and 2017
  for older codes), built into a small local table by a developer script, like the existing
  six-digit titles table.

## Capabilities

### New Capabilities
- `naics-subsectors`: the local table of 3-digit NAICS subsector titles, how it is built, and how
  a facility's code maps to its subsector.

### Modified Capabilities
- `emissions-inventory-tool`: the returned facility record carries `naics_subsector` and
  `naics_subsector_title`.
- `assessment-dashboard-state`: a facility in the workspace carries them.
- `web-ui-shell`: the Overview panel shows the three risk-by-group charts and their expand
  control (a new requirement in this capability).

## Impact

- Code: `scripts/build_naics_subsectors.py` and `data/naics_subsectors.csv` (new);
  `[industry]` settings (`subsectors_path`, columns) and `config/industry.py`;
  `tools/emissions/helpers/naics_subsectors.py` (new) and `tools/emissions/inventory.py`;
  `tools/schemas.py`; `api/schemas/workspace.py` and projectors; the exported contract and
  frontend types; `frontend/src/features/overview/` (a pure grouping module, a chart card, an
  expandable section, `OverviewPanel.tsx`).
- Dependencies: none added (Recharts 3.10.1 is already a frontend dependency, unused so far).
- Data: one new CSV (about 100 rows), built from two Census workbooks that are downloaded into
  `data/raw/naics/` (not committed), as for the existing titles table.
- Model view: two short strings more per listed facility.
- Out of scope: any new scientific calculation, ranking by emission rate, a per-group exposure
  map, and changing the ribbon, table or map.
