## Why

When the NEI has no stack for a facility, the next best evidence is a process-typical stack, found by describing the facility's industry to the SCC search (`lookup_scc_process_description`). That search matches text against SCC process descriptions, so it needs the industry's NAICS *title* in words ("Petroleum Refineries"); a bare code such as 324110 returns unrelated processes (checked: welding electrodes). Nothing supplied the title: TRI release rows carry no NAICS. Envirofacts holds both pieces: the primary NAICS code of every TRI submission (`tri_submission_naics`, `primary_ind = 1`) and the title of every code (`REF_NAICS`). The submission that matters is the one behind the emission record the agent is assessing, so the inventory must expose its control number, and it must only look at recent TRI years so old, stale submissions do not drive the assessment.

## What Changes

- Add a tool `fetch_facility_industry(doc_ctrl_num)` that returns the primary NAICS code of that TRI submission, its **title** (from `REF_NAICS`), whether the facility `reported` it or EPA `assigned` it, a source label and warnings.
- Fail closed: invalid number, no primary code, a placeholder (`999999`, "AFS Migration"), a missing title or a failed request give null values and a warning, never a guess or an exception.
- The emissions inventory returns the `doc_ctrl_num` of each record's submission and reads only the last 10 TRI reporting years (`[tri] recent_years`), applied in the request, not afterwards.
- The SCC lookup refuses a bare numeric NAICS code with a warning, strips a code written beside the words, and its description says the title is required.
- Tool descriptions say that an unknown industry or SCC ends in the EPA global default stack, and `calculate_exposure_metrics` reports `stack_source` and warns when the stack is generic (global default or PSTK), since a short cold stack gives far higher concentrations.
- Add an `[industry]` settings table with a typed loader.

## Capabilities

### New Capabilities
- `facility-industry-tool`: control number -> primary NAICS code and title.

### Modified Capabilities
- `emissions-inventory-tool`: recent-years window and the submission control number.
- `scc-process-context`: the lookup needs the industry in words and refuses a bare code.
- `exposure-metrics-tool`: `stack_source` and the generic-stack warning.
- `app-configuration`: new `[industry]` settings and `[tri] recent_years`.

## Impact

- Code: `tools/emissions/industry.py`, `tools/emissions/helpers/industry/naics.py`, `config/industry.py`, `config/loader.py`, `config/settings.toml`, `tools/schemas.py`, inventory helpers (`tri`, `reduce`, `lookup`), `tools/emissions/process.py`, `tools/emissions/rag/graph.py`, `tools/exposure/helpers/assessment.py`, `tools/exposure/metrics.py`, registry, README.
- Tests: helper, config, tool, description and window tests; a live smoke test (no key needed).
- Dependencies: none new. Data: none (titles come from Envirofacts).
