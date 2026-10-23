## Context

What exists (checked in the code):

- Each `Facility` in the workspace carries `exposure` ranges (`hq_worst`, `cancer_risk_worst`,
  `concentration_worst`, each `{low, high, low_stack, high_stack}`), a `status`, a `screening`
  outcome, `industry` (NAICS code and six-digit title), `conditions_of_use` and `lifecycle_stages`
  (previous change). `features/overview/resultsRows.ts` already turns a facility into a row and
  has `isAssessed`. The client settings carry `thresholds` (`hq_concern`, `cancer_lower`,
  `cancer_upper`).
- The Overview panel is `@container` based (`OverviewPanel` -> ribbon + `ResultsTable`); fullscreen
  is CSS-only so nothing unmounts; Escape belongs to the topmost layer.
- Recharts 3.10.1 is a declared frontend dependency with no usage yet.
- `data/naics_titles.csv` has only six-digit codes (1,151 rows). The Census 2-6 digit workbook
  (`https://www.census.gov/naics/2022NAICS/2-6%20digit_2022_Codes.xlsx`, 82 kB, same pattern for
  2017) lists every level; its first sheet has a leading `Seq. No.` column, then the code and the
  title, so the existing reader (which takes columns 1 and 2) cannot be reused as is.
- The frontend and API rules: show only values the API sent; no computing, converting or
  estimating scientific values; classification a UI needs comes from a tool, not from `api/`.

## Goals / Non-Goals

**Goals:** three top-5 bar charts (industry subsector, condition of use, life cycle stage) of the
worst-case HQ and cancer risk, hover with concentration and facility counts, expandable, using only
values the API sent.

**Non-Goals:** sums, means or any new exposure number; emission-rate ranking; changing existing
cards, table or map; sub-use or CDR-level groupings.

## Decisions

1. **What a bar is.** For each group, among its *assessed* facilities (outcome `full` or
   `worst_case_only`, i.e. the facility has `exposure`), the bar is the largest
   `hq_worst.high` (hazard quotient) and the largest `cancer_risk_worst.high` (cancer risk), each
   with the facility it came from. That is a max over values the API sent, the same kind of
   selection the ribbon's "highest worst case" card makes. Screened-out facilities are left out:
   their numbers are bounds, not results, and a group's bar would otherwise be a bound dressed as
   an assessment. Hover reports how many were left out. The hover concentration is that facility's
   `concentration_worst.high`; HQ and cancer risk are proportional to concentration for one
   chemical, so the stack with the highest HQ is the stack with the highest concentration.

2. **Grouping keys** (pure, `features/overview/riskGroups.ts`).
   - Industry: `facility.naics_subsector` + `naics_subsector_title`, label "325 · Chemical
     Manufacturing"; a facility without one is counted as "industry not reported", never grouped.
   - Condition of use: key `lifecycle_stage · cou_category` from `conditions_of_use`; a facility
     counts once per distinct key, so it can sit in several bars (the section says so). Facilities
     without conditions are counted as "no condition of use reported".
   - Life cycle stage: each entry of `lifecycle_stages`, likewise once per facility.
   `groupFacilities(facilities, by) -> Group[]` returns, per group: label, `facilities` (all),
   `assessed`, `screenedOut`, and the two `Best` records `{value, frsId, name,
   concentration}` or null. `topGroups(groups, rankBy, 5)` drops groups with no value for the
   ranking quantity, sorts descending (ties by label) and cuts to five. No arithmetic besides
   comparison and counting.

3. **Chart.** `RiskGroupChart.tsx` uses Recharts `BarChart` in a `ResponsiveContainer`, categories
   on the x-axis (labels wrap/truncate with a title attribute), two `Bar`s (HQ, cancer risk) with
   the project's accent and a second token colour (CSS variables, light/dark), two logarithmic
   y-axes (`scale="log"`), hazard quotient on the left and cancer risk on the right (found when
   looking at a first render: on one shared axis every bar is measured from a baseline set by
   the other quantity's range, which misleads), and `ReferenceLine`s at `hq_concern`
   (left axis), `cancer_lower` and `cancer_upper` (right axis) from the client settings; x-axis
   labels are angled and shortened. A value of 0 or below cannot be drawn on a log axis, so
   it is shown as no bar and still appears in the tooltip and the text table. The axis domain is
   the powers of ten around the data and the thresholds (axis geometry only). A custom `Tooltip`
   content function (a pure `describeBar`) gives: group, quantity and value, facility name and FRS
   ID, "worst-case concentration x µg/m³", "n facilities, m assessed" (and screened out). Recharts
   3's `accessibilityLayer` provides keyboard focus on bars. Beside the chart, a visually hidden
   `<table>` lists the same rows, which is also what the unit tests assert (jsdom has no layout, so
   `ResponsiveContainer` is mocked to a fixed size in tests and the chart is checked by its
   props and text).

4. **Ranking switch.** A two-button segmented control ("Rank by hazard quotient" / "Rank by cancer
   risk"), `aria-pressed`, in each section's header; the state is kept once in `OverviewPanel` so
   the three sections agree. Default hazard quotient (the same ordering the results table uses).

5. **Layout and expand.** `RiskGroupSection` (title, ranking switch, expand button, chart, note)
   inside a grid `grid-cols-1 @4xl:grid-cols-3` placed between the ribbon and the table. State
   `expanded: "industry" | "condition" | "stage" | null` lives in `OverviewPanel`. When set, the
   expanded section gets `col-span-full` and the available panel height (a flex column with the
   chart growing: `flex-1 min-h-[16rem]`), and everything else (ribbon, the other sections, the
   table) gets the `hidden` attribute, so all stay mounted and keep their state (the table's sort
   and fold). The expand button is `aria-expanded`, named "Expand section" / "Restore section".
   Escape restores: a keydown handler at the panel level that calls `preventDefault()` and
   `stopPropagation()` when a section is expanded, so the panel's fullscreen does not also exit
   (frontend rule: the topmost layer owns Escape). The ribbon, table and map are untouched apart
   from being hidden while a section is expanded.

6. **Subsector data and tool layer.**
   - `scripts/build_naics_subsectors.py`: reads the `2-6 digit_<year>_Codes.xlsx` workbooks from
     `data/raw/naics` with the standard library (zip + XML), finds the code and title columns by
     header text ("NAICS" with "Code", "NAICS" with "Title"), keeps three-digit codes, merges
     vintages newest-first, writes `data/naics_subsectors.csv` (`naics_subsector`, `title`,
     `vintage`) with `\n` endings. It shares the xlsx helpers of `build_naics_titles.py` only by
     import of its public functions where they fit and otherwise has its own sheet reader
     (the existing `read_workbook` is positional).
   - `[industry]` gains `subsectors_path`, `subsectors_code_column`, `subsectors_title_column`
     (`config/industry.py`, validated, tested).
   - `tools/emissions/helpers/naics_subsectors.py`: `subsector_titles(settings)` (read once, cached,
     read-only, setup errors raise like `naics_titles`) and `with_subsectors(records, titles)`
     setting `naics_subsector = code[:3]` (when the code has at least three digits) and the title.
     The reducer leaves both null (like `naics_title`), the tool fills them in `_titled`.
   - `EmissionRecord` gets `naics_subsector`, `naics_subsector_title`; the `query_emissions_inventory`
     docstring lists them.

7. **API and frontend types.** `EmissionPayload`, `Facility` and `_identity`/projectors carry the
   two fields (defaults null so saved state still validates); `export_contract` and `gen:types`
   regenerate the contract. The frontend `thresholds` already reach the Overview panel's parent
   (App holds the client settings); they are passed down as one prop.

8. **Tests.** Python: build script (headers by name, leading seq column, other levels dropped,
   vintage merge, reproducible bytes), config, `with_subsectors` (six-digit, short, missing,
   unlisted), record/lookup/inventory, API/state. Frontend (Vitest): `riskGroups` (max not sum,
   once per facility, several conditions, screened-out excluded, no value not ranked, ties, top 5,
   ranking switch, zero values), `describeBar`, the sections (two series and threshold lines,
   hidden table, tooltip text, "nothing assessed" message, ranking switch, expand/restore/Escape,
   hidden-but-mounted others, stacking class), and the Overview panel with all of it.

## Risks / Trade-offs

- **Max, not typical.** A bar is the worst facility in the group, so a group with one bad outlier
  looks as bad as one with many; the hover count and the assessed count keep that visible.
- **Overlap in the condition-of-use chart.** A facility can be in several bars, so bars are not
  additive; the section says so.
- **Cancer bar can be missing** for a chemical without a unit risk, and a group can have an HQ
  bar only; the tooltip says "no cancer risk reported".
- **Log axis hides small differences** among values near the thresholds; reference lines and the
  text table give exact values.
- **Few groups for life cycle stage** (at most about nine), so "top 5" may cut real groups; the
  section shows how many were not shown.
- **Data download.** Building the subsector table needs the two Census workbooks in
  `data/raw/naics` (not committed, like today); the resulting CSV is committed.
- **Recharts first use** in this app: bundle size grows; checked by `npm run build`.

## Open Questions

- Should screened-out facilities appear (clearly marked as bounds) in the bars? Left out now.
- Should the ranking switch be one shared control instead of one per section? Per section
  (shared state) is planned so an expanded section is self-contained.
