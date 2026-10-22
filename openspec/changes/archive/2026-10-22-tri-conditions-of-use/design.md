## Context

The inventory reads TRI through one paged Envirofacts request,
`/tri_reporting_form/tri_chem_info/tri_facility/tri_release_qty/tri_submission_naics/cas_registry_number/{casrn}/environmental_medium/{medium}/reporting_year/>/{after_year}/rows/{start}:{end}/JSON`
(`[tri].release_path`). `LatestReports` (`tools/emissions/helpers/inventory/reduce.py`) folds the
rows into one `Slot` per (medium, facility): the latest year, with several same-year reports added
together and the highest control number kept. The tool layer then adds NAICS titles
(`naics_titles`/`with_titles`) and, since the last change, injects operating hours (`hours_for`).

What I verified against the live API and the files while planning:

- **`tri_chem_activity`** (Envirofacts `TRI_CHEM_ACTIVITY`): one row per `doc_ctrl_num`, with 15
  flag columns: `produce`, `imported`, `used_processed`, `sale_distribution`, `byproduct`,
  `manufacture_impurity` (Section 3.1a-f), `reactant`, `formulation_component`,
  `article_component`, `repackaging`, `process_impurity`, `processed_recycling` (3.2a-f; the
  column-to-letter order follows the Form R, and is also the crosswalk's section letters),
  `chem_processing_aid`, `manufacture_aid`, `ancillary` (3.3a-c). Values are the strings "0"/"1",
  but `process_impurity` came back as the integer 0 and `processed_recycling` as null.
- **Joining it adds columns, not rows.** Appending `/tri_chem_activity/` after
  `tri_submission_naics/` returned identical row and control-number counts for: benzene 2023
  (1,070 / 940 docs), lead 2022 (1,501 / 1,328), formaldehyde 2021 (2,331 / 1,988),
  n-hexane 1990 (3,001 / 2,890), lead 2020 (3,001 / 2,673; both capped at the probe's 3,000-row limit).
  No control number was lost to the (inner) join in any of them. Rows exceed docs only because of
  secondary NAICS codes, which the reducer already drops.
- **No sub-use table.** `TRI_CHEM_SUBUSE`, `TRI_SUBUSE`, `TRI_CHEM_ACTIVITY_SUBUSE` and five
  similar names return 404, so the sub-use codes (P101 ... Z399) the finer crosswalk levels need
  are not available here.
- **The crosswalk** (`data/tsca_cou_cdr_tri_crosswalk.csv`, 480 rows, 20 columns) is keyed on the
  TRI side by `tri_form_r_section` ("Part II Section 3.2b"), `tri_activity_category`,
  `tri_file_1b_field` and `tri_subuse_code`. Rows at `mapping_level == "1_lifecycle_stage"` with no
  sub-use code give one row per Section 3 activity (plus a "3.3 (a, b, c)" parent and one extra
  row, 3.3c -> Commercial use / Product category, Partial). Strengths: Direct, Partial, Inferred,
  None (CDR exempt). The file is untracked in git today.

## Goals / Non-Goals

**Goals:** per facility, the TSCA life cycle stages and conditions of use implied by the activities
its latest submissions report, from the same TRI request, without double counting any release;
shown in the workspace; mapping done internally, no new tool.

**Non-Goals:** CDR function/product level (needs sub-use codes); using conditions of use in the
risk numbers; the Disposal/release rows of the crosswalk; changing which facilities are returned.

## Decisions

1. **Same query, one more join.** Edit `[tri].release_path` to add `/tri_chem_activity` after
   `tri_submission_naics`. Why this is safe: the table is 1:1 with control number, the probes above
   lost no control number and added no row, and the reducer already drops secondary-NAICS rows.
   It is an inner join in Envirofacts; if a submission ever had no activity row it would vanish from
   the inventory. So the guard is a test plus a runtime stat: the reducer counts rows with none of
   the activity columns ("activity data not returned") and the inventory warns, so a regression in
   the join is visible. (A left join is not available in the path syntax.) Rejected: a second
   request per control number (hundreds of calls), or a second bulk request by chemical (a second
   paged scan and a merge on control number for no benefit).

2. **No duplicate rows by construction.** The reducer never stores activity rows, only a
   `frozenset` of section keys per `Slot`. `Report` gains `activities: frozenset[str]` (parsed from
   the row's flags); a new slot takes the report's set; `_combine` (same year) unions; `_take_year`
   (later year) replaces; an earlier-year report is ignored, as it is for quantity. Union (rather
   than "the kept submission's activities") because the slot's quantity is the sum of all those
   same-year reports, so the activities that explain that quantity are theirs together.

3. **Parsing flags (`reduce.py`, config-driven).** `[conditions_of_use.flags]` maps flag column ->
   Form R section key, e.g. `produce = "3.1a"`. A flag is set only if its value is `1`, `"1"` (after
   strip), never a bool, never other text. Missing columns -> no activity, and if none of the
   configured columns is present in a row, the report is flagged `activity_columns_seen = False`
   so the slot can say "not returned" instead of "none reported".

4. **Mapping (`tools/emissions/helpers/inventory/conditions.py`).**
   `load_crosswalk(settings) -> Crosswalk` reads the CSV once with the standard `csv` module
   (cached per settings like the plant-hours baseline), keeps rows where `mapping_level` equals
   the configured level and `tri_subuse_code` is empty, and builds
   `dict[section_key, tuple[Condition, ...]]` in file order. The section key is the crosswalk's
   `tri_form_r_section` normalised to "3.2b" with a regexp (`Part II Section (3\.[123][a-f])`);
   rows whose section does not match a configured flag (the "3.3 (a, b, c)" parent, Section 4.5
   NAICS rows) are not indexed. `Condition` is a frozen dataclass; the record carries it as a
   `ConditionOfUse` TypedDict: `tri_activity`, `tri_section`, `lifecycle_stage`, `cou_category`,
   `mapping_strength`. `ConditionsMapper.__call__(activities: frozenset[str], seen: bool) ->
   Conditions(conditions, stages, note)` sorts sections ("3.1a" < "3.2b" < "3.3c" lexical order
   works), emits each crosswalk row once, deduplicates identical conditions, and lists distinct
   stages in order of first appearance. An activity whose section has no crosswalk row is dropped
   and counted into one warning (logged once).

5. **Injection, like operating hours.** `Reducer.records(..., conditions_for=None)` takes a
   `ConditionsFor = Callable[[frozenset[str], bool], Conditions]`; `None` gives empty lists and a
   note "conditions of use not requested". `lookup_emissions(..., conditions_for=...)` forwards it
   and `tools/emissions/inventory.py` builds the mapper at the edge from
   `get_conditions_settings()` and the cached crosswalk. The reducer imports neither the CSV nor
   the settings. Keeping the 18-line function limit in mind, the record assembly in `_reported`
   spreads a small `_Conditions` TypedDict like `_Where`.

6. **Record, API and UI.** `EmissionRecord` gains `conditions_of_use: list[ConditionOfUse]`,
   `lifecycle_stages: list[str]`, `conditions_note: str | None`. `api/schemas/workspace.py` adds a
   `ConditionOfUse` model and the three fields on `Facility` with defaults (empty/None) so older
   saved state still validates; `EmissionPayload` and `_attached`/`_release` pass them through;
   `scripts/export_contract.py` and `npm run gen:types` regenerate the contract. In
   `FacilityHoverCard.tsx` a "Conditions of use" section lists the stages as chips and each
   condition as "activity -> COU category" with its strength; empty shows "not reported" plus the
   note (frontend rule: absent is never an empty-looking result). The workspace computes nothing.

7. **Config.** `[conditions_of_use]` + `config/conditions_of_use.py`:
   `crosswalk_path = "data/tsca_cou_cdr_tri_crosswalk.csv"`, `level = "1_lifecycle_stage"`,
   column names (`level_column`, `section_column`, `subuse_column`, `stage_column`,
   `category_column`, `strength_column`, `activity_column`), `section_pattern`, and
   `[conditions_of_use.flags]` (15 entries). Validators from `config/parsing.py`: flags non-empty,
   unique columns, sections match `3.[123][a-f]`. `release_path` stays validated by the existing
   TRI loader.

8. **Tool text and model view.** `query_emissions_inventory`'s docstring describes the three new
   fields in plain words (what a condition of use is, that several can apply, that "None (CDR
   exempt)" strengths are not conditions of use in the CDR sense, that an empty list has a reason in
   `conditions_note`). The prompt is not changed (it teaches reasoning, not fields); the
   conditions appear in the report only if the model chooses to use them.

9. **Tests.** Reducer: flags -> set (1, "1", 0, null, "yes", True, 2), union within a year,
   replacement by a later year, ignoring an earlier year, secondary-NAICS rows still dropped,
   repeated rows, no activity columns at all (note), all zeros (note). Mapper: each spec scenario
   against a small synthetic crosswalk (placeholder text) plus a test against the real CSV that
   every configured flag has at least one level-1 row and the 3.3c double mapping is returned.
   Lookup/tool: the request path contains the join; same rows with the join as without (fixture
   built from two recorded pages); the record carries the fields. API/projector/serializer and a
   Vitest test for the card. The existing fixture `tri_rows.json` has no activity columns, which
   exercises the "not returned" path.

## Risks / Trade-offs

- **Inner join regression.** Described in decision 1; guarded by a stat/warning and tests, not by
  the API. Probed on five chemical/year combinations with no loss.
- **Request size.** About 15 small fields per row (a few percent of a row that is already ~5 KB),
  so `page_size` stays 1000. Re-time one live lookup when applying.
- **Mapping strength is weak for some rows** (Partial: on-site use, byproduct, sale/distribution,
  recycling; "None (CDR exempt)": impurities). The record keeps the crosswalk's strength so the UI
  and the report can caveat; nothing is upgraded.
- **Activities are per submission, not per release.** A facility with several submissions in the
  year gets the union; a condition may not apply to every kilogram of the summed release.
- **Model context.** Up to 25 listed facilities each carry a few condition entries; kept short on
  purpose (short strings, no crosswalk notes or sources).
- **Crosswalk is a snapshot** of EPA's mapping as built by the repo's author (RY2023 file layout);
  new TRI activity columns would need a config entry.

## Open Questions

- Should "Disposal" (the crosswalk rows for release and waste management) be shown for every
  facility with a release? It is not derived from Section 3 activities, so it is left out here.
- Should the hover card also show the crosswalk's mapping strength as text or a visual cue? The
  plan shows it as small text; a visual treatment can follow.
