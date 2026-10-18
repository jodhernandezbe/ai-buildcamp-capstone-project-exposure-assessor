## Context

Checked live (2026-10-18). `tri_submission_naics/primary_ind/1/doc_ctrl_num/{doc}/JSON` returns exactly one primary row per submission (183 of 183 checked) with `naics_code`, `naics_sequence_num`, `primary_ind`, `source` ("Reported" or "ASSIGNED") and `method` (XWALK, COMMERCIAL, "RY 2006 DATA"). EPA assigns codes to older submissions by crosswalk, often generic ones (1388025696232 -> 335999); facilities report their own from 2006 (1313211440122 -> 313310, "Textile and Fabric Finishing Mills"). `REF_NAICS/NAICS_CODE/{code}/JSON` gives `naics_desc`; "999999" is "AFS Migration", a placeholder. The control number is on the TRI release rows the inventory already reads (`doc_ctrl_num`), and characters 3 and 4 of it are the reporting year. The release query accepts a `reporting_year/>/N` filter (the operator is URL-encoded as `%3E`).

## Goals / Non-Goals

**Goals:** give the agent the industry in words from the submission behind the record it assesses; fail closed; keep the SCC search from silently returning nonsense for a code; keep the EPA global stack as the final fallback and say when it is used.
**Non-Goals:** NAICS on every inventory record (1 to 4 s each); using NAICS to filter NEI stacks (one NAICS per facility cannot separate stacks); a NAICS-to-SCC crosswalk.

## Decisions

**D1. A separate tool keyed by control number.** The inventory returns up to hundreds of facilities; the agent assesses a few. The tool takes the `doc_ctrl_num` of the chosen record, so the industry is the one of the year the emission belongs to (not a guess among years). Two requests per record: code, then title, through the shared `EfserviceClient`.

**D2. Primary row.** Keep rows with `primary_ind = 1`; choose the lowest `naics_sequence_num`, then the smaller code, and warn if several differ. Placeholders (`999999`) are dropped; if nothing remains the result is null with a warning.

**D3. Origin.** `source` "Reported" -> `code_origin` "reported", "ASSIGNED" -> "assigned" (warning: EPA assigned it, it may be generic). The previous design (rank all submissions of a facility by year read from the control number) was dropped: the inventory already knows the submission.

**D4. Ten-year window in the request.** `[tri] recent_years = 10`; the release path filters `reporting_year/>/{after_year}` with `after_year = current year - recent_years`. Rows outside the window never arrive; the reducer also counts and warns about any that do. Done now, not later, because filtering later lets old reports win the "latest per facility" step and break the chain to the control number. The same-year combine keeps the highest control number, and a form with no quantity does not lend its number.

**D5. The SCC guard.** `validate` drops numeric tokens and label words beside a number and refuses a code-only description with a warning.

**D6. Generic stacks are named.** The fallback chain is NEI -> PSTK by SCC -> EPA global default (3 m, 0.2 m, 4 m/s, 295.4 K). `ExposureMetrics.stack_source` echoes `StackParameters.source`; the global default and PSTK add a warning that the stack is not the facility's own and gives much higher concentrations (checked: about 1000 times a real tall stack).

## Risks / Trade-offs

- [Industry is not process.] A NAICS says what is made, not which unit emits; SCC matches are candidates.
- [Assigned codes are generic.] They are flagged `assigned`; the agent is told to treat them as weak evidence.
- [Window drops stale facilities.] A facility that stopped reporting more than 10 years ago is absent from the inventory; the description says so.
- [Envirofacts latency.] Two requests per selected facility.
