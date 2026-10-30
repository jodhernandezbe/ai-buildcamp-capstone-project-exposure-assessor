## Context

See proposal.md for motivation. Current state that shapes the approach:

- The TRI release query keeps only `AIR STACK` (`[tri].media`); `AIR FUG` is a one-line
  config change away but is not read. The emission rate already divides the stack release by
  Census QPC hours (`PlantHours`, `data/census_qpc_baseline.parquet`, hours/week by NAICS prefix),
  so "use t_op instead of 8,760" is largely done; what is missing is days/week, the schedule
  and the provenance field.
- TSCA life cycle stage and condition of use already come from TRI Section 3 flags through
  `data/tsca_cou_cdr_tri_crosswalk.csv` (`conditions_of_use` on each record). That crosswalk is
  keyed by activity, not NAICS.
- PubChem PUG View is fetched and cached once per compound (`tools/informatics/helpers/pubchem/`,
  headings configured in `[[pubchem.fields]]`); molecular weight is already extracted.
- Per-facility chain: `tools/assessment/helpers/chain.py` builds a `FacilityAssessment` whose
  `exposure` is the ambient result; `api/services/projectors/` turn tool results into the
  workspace the frontend reads; `frontend/src/types` is generated from the API schema.
- Rules in CLAUDE.md files: pure physics in `models/` with units; URLs, headings, numbers in
  `config/`; no invented numeric data; functions at most 18 lines; tools do not import other
  tool folders (only `tools/assessment/` composes them); the user asked for the Overview and
  hover card to change, so the "leave dashboard panels alone" preference does not apply here.

## Goals / Non-Goals

**Goals:**
- Worker screening per facility from data the app already touches, additive to the community result.
- Every constant (ventilation tiers, breathing volumes, tenure, thresholds, shift length) in config.
- Fail closed: a missing input gives null with a reason, never a default that looks like data.

**Non-Goals:**
- Ranking or screening out facilities by the occupational result (tiering stays community-driven).
- Facility-specific ventilation, process-specific ChemSTEER release models, dermal or oral worker routes.
- Scraping NIOSH/OSHA sites; PubChem is the only source of limits.
- Redesigning the Overview beyond the new switch and badges.

## Decisions

**1. Map the request's file names onto the existing layout.** `models/occupational.py` becomes
`models/exposure/occupational.py` (the folder already holds inhalation and risk). The PubChem
parser extension lives in `tools/informatics/helpers/pubchem/` (a new `limits.py` beside
`extract.py`, using the same record walker and `read_statement`), not a new `tools/chemicals/`
tree. The schedule/COU resolver lives in `tools/emissions/helpers/inventory/` (next to
`plant_hours.py`) with its settings in `config/`. `EPAExecutiveOverview.tsx` is
`features/overview/OverviewPanel.tsx` plus a new card; the SSE route is the existing chat
stream. Alternative, creating the requested paths verbatim, would break the layering rules
and duplicate existing code.

**2. Reuse the QPC baseline; no `CENSUS_QPC_NAICS_SCHEDULES` dict.** The request asks for a
hand-stored table of days/week and hours/week for ~13 prefixes. The repo already holds the real
Census figures by four-digit NAICS (hours/week), built reproducibly from the published workbook,
and CLAUDE.md forbids hard-coding data in Python and inventing numbers that look real. The QPC
survey does not publish days per week, so days/week is derived: `ceil(hours_per_week / shift_hours)`
capped at 7, `shift_hours` configured (8). Weeks per year configured (52.14, giving 8,760 h at
168 h/week). The source string says "days per week derived". Alternative: ask for a table of
days per week by sector from another source; rejected as unsourced.
Consequence: the non-manufacturing sectors named in the request (211, 2211, 4246, 562) get
a schedule only if the baseline has them; otherwise the configured default schedule applies and is
disclosed.

**3. Schedule defaults.** When no baseline row matches, the schedule is a configured default
(continuous: 7 d/wk, 24 h/day, 8,760 h/yr, the current default behaviour). With continuous
operation the box-model generation spreads over 8,760 h, which understates the worker
concentration relative to a single-shift plant; this is stated in the assumptions.

**4. CDR industrial sector needs a data file, built once.** NAICS to IS (the CDR industrial
sector list in EPA's CDR instructions, Appendix D) is not in the repo. Add
`data/cdr_naics_industrial_sector.csv` with columns for NAICS prefix, IS code, name and the CDR
vintage, produced by a small script from the EPA publication (same pattern as
`scripts/build_census_qpc_baseline.py`), validated on load, longest-prefix matched with the
existing `commons.prefix.longest_prefix`. If the publication cannot be turned into a clean
table during apply, the file ships with only rows that were verified and the rest stay null;
nothing is filled in from memory. Life cycle stage and COU come from the existing
activities (Decision not to map them from NAICS: a NAICS code says the industry, not what the
facility does with this chemical).

**5. Fugitive release rides the existing inventory path.** Add `"AIR FUG"` to the
configured media list and split the fetched rows by medium: stack rows build the facilities and
rates exactly as before; fugitive rows are folded into the record as
`fugitive_release_kg_per_year` through the shared unit conversion. One extra paged request per
chemical (the media loop already makes one per medium). The record cache key includes the media,
so cached inventories refresh. Alternative: a separate fugitive tool; rejected, it would give the
model another call to make and break "one inventory per chemical".

**6. PubChem limits: one parse, more fields.** The PUG View response is already fetched and
cached; limits are read from the same record (no extra request). A new config table
`[[pubchem.limits]]` names each limit's heading path, kind (TWA, STEL, IDLH, PAC level) and
programme; the request's heading names are the starting set and the real PUG View headings are
confirmed against a live record during apply (the smoke test in `tests/smoke`). Units: ppm to
mg/m^3 at 25 degC with 24.45 L/mol (config) using the already-extracted molecular weight, reusing
`commons.units` for mass/volume conversions. Selection order OSHA, NIOSH, ACGIH is config as a
list. PubChem often holds limits as free text ("TWA 10 ppm (35 mg/m3)"); the reader takes a
statement only if it has one number and unit, otherwise tries the parenthesised mg/m^3 only
when it is unambiguous, else skips with a reason (same fail-closed stance as the property reader).
The result type is a new `OccupationalLimits` TypedDict in `tools/schemas.py`.

**7. Occupational model is pure and separately configured.** `models/exposure/occupational.py`
takes numbers only (no config reads). A new `config/occupational.py` loader holds the two
ventilation tiers (ft^3/min and mixing factor), breathing volumes (10 and 20 m^3/day), worker
days (250), tenure (40 y), lifetime (78 y) and tier thresholds (1, 0.1; 1e-4, 1e-6). Conversion of
ft^3/min uses Pint via `commons.units`, not the request's rounded 1.416 / 0.236 constants.
Formula note: with the request's equations the tenure cancels in ADC (tenure over tenure x 365),
so ADC = TWA x 0.5 x OD_worker / 365 and LADC = TWA x 0.5 x OD_worker x ED / (78 x 365); the model
implements exactly that, and a test pins the cancellation. CR uses LADC (mg/m^3) x 1000 x IUR
(per ug/m^3), consistent with the repo's ug/m^3 IUR. The "worker days" is min(250, operating days).

**8. Wiring: a sibling to the ambient step, not inside it.** `calculate_exposure_metrics` keeps
its signature and result (the model-facing tool is unchanged, no regression in agent behaviour).
The occupational screening is an internal step of `tools/assessment/` (the only package allowed
to compose tool folders), run in `chain.py` for each evaluated facility with the facility record
(fugitive release, schedule), the chemical's limits and toxicity. The `FacilityAssessment` gains
`community_exposure` (the current `exposure` value, kept under the old key too for one release
to avoid breaking projectors and evals, then removed in the same change if tests allow),
`occupational_exposure` and `operational_profile`. A standalone `calculate_occupational_exposure_metrics`
tool is not added: the model would then have to call it per facility; the assessment already
runs per facility and the program, not the model, holds the complete result. The model's
text view gets one line per facility (tier and ratio) and the tool description/system prompt
are updated to teach reading it (prompt describes reasoning, not tool order).

**9. Workspace and generated types.** `api/schemas/workspace.py` gets `OccupationalExposure` and
`OperationalProfile` models on `Facility`; a projector in `api/services/projectors/` fills them from
the assessment artifact under the existing validation rules; the schema export regenerates
`frontend/src/types`. The browser only formats numbers it is given.

**10. Frontend: the worker result lives with the community result.** No separate view, tab or
facility picker. The worker screening is evaluated for every assessed facility like the stack
result, so it is shown where the stack result is: a "Worker exposure" card in the summary
ribbon (the highest limit ratio, hazard quotient and cancer risk over all facilities, naming
the facility, from a `worker_risk` summary the API selects from the tool values, as it does for
`risk`); a compact badge (community HQ beside worker tier and R_OEL) and a "Worker exposure"
section in the facility inspector; and a ring around each map marker coloured by the worker
tier (the fill stays the community status), explained in the legend and in the marker's
accessible name. Colours use existing tokens; the tier is always written as text too. "Risk by
group" is unchanged for now (see Open Questions).

**11. Vapor pressure is context, not an input.** The chemical's vapor pressure (mmHg) is read
from the chemical properties the assessment already holds (CompTox first, PubChem fallback, the
existing source order and `source` string), so there is no new request and PubChem's
`vapor_pressure` field is reused unchanged. It is attached to `occupational_exposure` with its
source, and a configured `low_volatility_mmhg` threshold in `[occupational]` adds a plausibility
warning. It does not enter the equations: turning it into a generation rate would need process
area, temperature and air speed that no public source gives us. Alternative: cap the generation
rate with an evaporation estimate; rejected as it needs invented defaults.

## Risks / Trade-offs

- [Derived days/week is not a survey value] → source text says "derived", shift length is config,
  and the schedule only scales the box-model rate; tests pin the derivation.
- [Fugitive generation over operating hours may overstate or understate real concentration; the
  ventilation tiers are generic] → shown as screening, tiers labelled, assumptions in the result.
- [PUG View headings and text vary by compound] → fail-closed reader, live smoke test, null with
  reason; the TWA may be missing for many chemicals, so the ratio is often null and the tier then
  depends on HQ and CR.
- [Extra TRI request slows each lookup (~11 s per 1000 rows)] → fugitive rows are fewer; the
  paged fetch and the existing result cache are reused; measure during apply.
- [A larger `FacilityAssessment` increases snapshot and cassette churn in evals] → keep
  `exposure` readable during the transition; re-record cassettes once; run evals 3x.
- [CDR sector table coverage may be partial] → null with reason, never inferred.
- [Chemicals with a CAS but a TRI category (no discrete fugitive row)] → the category path
  returns fugitive rows for the category code like stack rows; the disclosure already applies.

- [Vapor pressure values from CompTox and PubChem can disagree or be at another temperature] → the existing property rules (temperature window, agreement ratio) apply; the value only drives a warning.

## Migration Plan

Additive. Order: model and config, limits parser, inventory medium and schedule, assessment
wiring, API schema and generated types, frontend. Roll back by reverting the commit; the only
data change is the new CSV. Cached inventories keyed without the new medium are ignored after the
key change. No stored user data is affected.

## Open Questions

- Which edition of the EPA CDR instructions to take the sector list from (2020 vs the current
  reporting cycle); the loader records the vintage either way.
- Whether the "Risk by group" charts should also rank the worker quantities (limit ratio, worker HQ and cancer risk), which needs the worker thresholds in the client settings.
- Whether the weeks-per-year constant should follow the QPC convention (52.14) or 52; both
  fit in config.
