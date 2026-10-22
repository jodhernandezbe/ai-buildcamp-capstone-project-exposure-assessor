## Why

A facility's release only means something in the context of what it does with the chemical.
TRI already records that: each Form R says whether the facility produces, imports, processes
(as a reactant, formulation component, article component, ...) or otherwise uses the chemical.
EPA's TSCA risk evaluations call that a *condition of use* within a *life cycle stage*, and
`data/tsca_cou_cdr_tri_crosswalk.csv` maps the TRI activities to them. Today the inventory shows
none of it, so the assessment cannot say under which TSCA conditions of use a facility's release
occurs. A facility can report several activities for one chemical, so it can have several
conditions of use and life cycle stages.

## What Changes

- Add the Envirofacts table `tri_chem_activity` (one row per submission, one 0/1 flag per Form R
  Section 3 activity) to the TRI release query that the inventory already makes, as one more join
  on the submission's control number. It adds columns, not rows: five probes (four chemicals, 1990 to 2023) returned
  the same number of rows and control numbers with and without it (e.g. 1,070 and 2,331 rows), and the table has exactly one row
  per control number. The reducer also folds activities in as a set per facility, so a repeated
  row can never repeat a condition.
- Read the 15 Section 3 flags (3.1a-3.1f manufacture, 3.2a-3.2f process, 3.3a-3.3c otherwise use)
  of the submissions that make up a facility's latest-year release, and take the union.
- Map each reported activity to its TSCA life cycle stage and condition-of-use category with the
  crosswalk CSV, internally, in the inventory (no new tool). The crosswalk is joined on the Form R
  section and only its life-cycle-stage level (`1_lifecycle_stage`) is used, because Envirofacts has
  no sub-use table (the finer CDR function/product rows need TRI sub-use codes, which Envirofacts
  does not expose; `TRI_CHEM_SUBUSE` and similar names return 404).
- Each emission record gains `conditions_of_use` (activity, Form R section, life cycle stage, COU
  category, mapping strength), `lifecycle_stages` (the distinct stages), and `conditions_note`
  (why the list is empty, when it is).
- Show them on the facility in the workspace (API payload, contract, and the facility inspector).
- Put the crosswalk path and column names, the level used, and the flag-to-section table in a
  `[conditions_of_use]` section of `config/settings.toml`; the query path stays in `[tri]`.

## Capabilities

### New Capabilities
- `tri-conditions-of-use`: reading TRI Section 3 activities without duplicating rows and mapping
  them to TSCA life cycle stages and conditions of use through the crosswalk.

### Modified Capabilities
- `emissions-inventory-tool`: the returned facility record carries the conditions of use, life
  cycle stages and the note.
- `assessment-dashboard-state`: a facility in the workspace carries them.
- `web-ui-shell`: the facility inspector shows them.

## Impact

- Code: `config/settings.toml` (`[tri].release_path`, new `[conditions_of_use]`),
  `config/conditions_of_use.py` (new); `tools/emissions/helpers/inventory/` (`conditions.py` new;
  `reduce.py`, `lookup.py` fold activities and take an injected mapper); `tools/emissions/inventory.py`
  builds the mapper at the edge; `tools/schemas.py`; `api/schemas/workspace.py` and projectors; the
  exported contract and frontend types; `frontend/src/features/map/FacilityHoverCard.tsx`.
- Data: reads `data/tsca_cou_cdr_tri_crosswalk.csv` (already in the repo, currently untracked, so it
  is committed with this change); no new dependency.
- Request size: ~15 more fields per TRI row; the page size and cap are unchanged. To be confirmed
  against the live API when applied (the TRI call is already the slow one).
- Model view: each listed facility's record gets a few short entries, which makes the inventory
  text the model reads somewhat longer; the tool description says how to read them.
- Not in scope: sub-use level mappings (CDR function and product codes), the "Disposal" and
  "Distribution" rows beyond the Section 3.1d flag, any use of conditions of use in the risk
  calculation, and a new tool.
