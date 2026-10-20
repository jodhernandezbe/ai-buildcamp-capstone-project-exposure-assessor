# Exposure Assessor

An AI Engineering Buildcamp capstone project that turns fragmented environmental data into screening-level chemical exposure risk profiles.

## The Problem

Public health researchers, environmental risk assessors, and community advocates often struggle to rapidly evaluate localized chemical exposure risks because critical data on industrial releases, chemical properties, and environmental transport variables are siloed across multiple disparate databases.

## What It Does

Exposure Assessor unifies public datasets, such as the EPA Toxics Release Inventory (TRI), with phenomenological transport models to automate screening-level exposure assessments. A user provides a location, facility, or chemical of interest, and the system pulls together release data, chemical properties, and transport modeling to return an actionable risk profile — transforming siloed environmental data into a starting point for further investigation.

## Setup

1. Install uv if you don't have it yet: https://docs.astral.sh/uv/getting-started/installation/

2. Clone this repository (or download the zip and extract it).

3. Create a `.env` file from the template and add your API key:

       cp .env.example .env

4. Install dependencies:

       uv sync

5. Verify the setup:

       uv run pytest

## Architecture

The code is split into four packages with one-way dependencies: `agent` -> `tools` -> `models`, and `agent` -> `prompts`. `models` knows nothing about LLMs or LangChain.

    agent/
      graph.py               build_agent(model, ...) -> compiled LangGraph
      state.py               AgentState (message history)
    commons/                 generic pure utilities shared across layers (units.py: Pint)
    models/                  pure NumPy physics, no LLM/LangChain imports, grouped by what they model
      transport/             dispersion.py (sigmas, Gaussian plume), plume_rise.py, wind_profile.py,
                             screening.py (SCREEN3-style worst case over weather and distance)
      weather/               stability.py (Pasquill-Gifford class), meteorology.py (hourly summary)
      receptors/             population.py (areal scaling, age bands)
      exposure/              dose.py (ADD, LADD), inhalation.py (exposure concentration, doses,
                             HQ and cancer risk), risk.py (emission rate, risk ratios)
    prompts/
      registry.py            load_prompt(name) reads prompts/<name>.md
      agent_system.md        system prompt (XML-tagged sections)
    tools/
      registry.py            ToolRegistry + ALL_TOOLS / get_all_tools()
      schemas.py             TypedDicts shared by tool inputs/outputs
      informatics/properties.py   fetch_chemical_properties
      emissions/inventory.py      query_emissions_inventory
      emissions/industry.py       fetch_facility_industry (TRI control number -> NAICS title)
      emissions/process.py        lookup_scc_process_description (NAICS text -> SCC processes)
      emissions/stack.py          fetch_stack_parameters_from_nei (tier 1: NEI candidates), _from_scc (tier 2)
      emissions/rag/              SCC retrieval: embeddings, Chroma index, LangGraph graph
      emissions/helpers/          inventory/ (TRI paging, reduction, rate), stack/ (PSTK, NEI, FRS-to-EIS),
                                  efservice.py (shared Envirofacts client)
      exposure/meteorology.py     get_meteorological_boundary
      exposure/population.py      get_population_receptors
      exposure/metrics.py         calculate_exposure_metrics
      exposure/helpers/           meteorology/ (Open-Meteo, conditions), population/ (Census, estimate),
                                  assessment.py, inputs.py
      http.py, digits.py          shared by the tool folders (retrying JSON client, digit-string ids)
    tests/                   pytest suite, mirrors the package layout

The intended tool flow for an assessment: chemical properties -> emissions inventory -> stack parameters -> meteorology and population -> exposure metrics. `fetch_chemical_properties` is implemented (CAS -> SMILES -> CompTox, with Pint unit conversion to fixed units), and so is `query_emissions_inventory` (CAS -> EPA TRI facilities with their latest reported stack-air release, location and an average emission rate in g/s at 8760 operating hours per year, configurable in `config/settings.toml`; only the last 10 TRI reporting years, `[tri] recent_years`, are read, and each record carries the `doc_ctrl_num` of its TRI submission; a facility whose TRI rows have no coordinates, common since TRI stopped collecting them, gets them from its FRS record, `GEO_FACILITY_POINT`, at one extra request each). `fetch_facility_industry` takes that control number and returns the submission's primary NAICS code and its title in words (Envirofacts `tri_submission_naics` with `primary_ind = 1`, titles from `REF_NAICS`), saying whether the facility reported the code or EPA assigned it; the title is what `lookup_scc_process_description` needs, since a bare code is refused. When the industry or the SCC is unknown the chain ends in the EPA global default stack, and `calculate_exposure_metrics` reports `stack_source` and warns that such a stack is generic and gives much higher concentrations. `fetch_stack_parameters_from_scc` returns EPA PSTK stack defaults for an SCC (a PSTK CSV is expected at `[stack.pstk].path`), falling back to the AirToxScreen global point-source default, and `lookup_scc_process_description` finds candidate SCC process descriptions for a NAICS description by semantic search over `data/epa_scc_to_epa_emission_sector.csv.gz` (a compact, gzip-compressed copy of the raw EPA table with only the needed columns and the Point rows; rebuild it from the raw download in `data/raw/` with `uv run python -m scripts.compact_scc_table`) (OpenAI embeddings, `OPENAI_API_KEY`; the index is cached in `.cache/scc_index` and can be pre-built with `uv run python -m scripts.build_scc_index`). `fetch_stack_parameters_from_nei` (tier 1) takes a facility's FRS ID, finds its EIS facility ID(s) with the Envirofacts `FRS_PROGRAM_FACILITY` table, and returns the facility's distinct NEI stacks as candidates (real records, never averaged; near-identical ones merged, lowest stack first, at most `[stack.nei].max_candidates`), which the agent passes together to one exposure calculation; with none it falls back to the SCC tool. The NEI stacks come from `data/nei_stacks/` (gzip CSV shards named by the first digit of the EIS ID, about 1.4 MB in total), built from the 2023 NEI SMOKE point flat file: put `nei_smoke_point_2023.zip` in `data/raw/` (git-ignored) and run `uv run python -m scripts.compact_nei_stacks`. The shard values are in the SMOKE FF10 units (ft, ft, ft/s, degF; `[stack.nei.units]`) and are converted with Pint. Roughly a quarter of TRI facilities have NEI stack data (the rest have no EIS ID or only fugitive/blank release points). All Envirofacts requests share one throttled, retrying client configured in `[efservice]`. `get_meteorological_boundary` (latitude, longitude, optional year) summarizes one year of hourly ERA5 reanalysis from the Open-Meteo historical archive (no API key; `[meteorology]` in `config/settings.toml`): annual mean 10 m wind speed (not below a configured minimum), prevailing wind direction (most frequent 10 degree sector), the most frequent Pasquill-Gifford class (EPA's SRDT key by day and Turner's key at night, EPA-454/R-99-005) and the annual mean temperature in K. These are annual representatives on a roughly 25 km grid, not worst-case conditions. When the inputs are invalid or the archive cannot be used it returns a configured screening default, labelled `source: "screening default"` with a warning saying why. The free Open-Meteo tier is for non-commercial use (under 10,000 calls a day) and requires attribution (CC BY 4.0). `get_population_receptors` (latitude, longitude, optional radius in km, default one mile) estimates the residents around a point and their age mix (0-4, 5-17, 18-64, 65+ as percent): it finds the census tracts that intersect the circle (Census TIGERweb), reads their ACS 5-year counts (Census Data API, vintage in `[population]`) and scales the total by circle area over tract land area, which assumes people are spread evenly over the tracts. **The Census Data API needs a free API key** (https://api.census.gov/data/key_signup.html): set `CENSUS_API_KEY` in `.env` (see `.env.example`); without it every request is redirected to a "Missing Key" page. Tracts whose ACS estimates are missing are left out and counted in `warnings`. When the input is invalid, the key is missing or refused, a service fails, or no census tract exists (open water, outside the United States) it returns a configured screening default, labelled `source: "screening default"` with a warning saying why. ACS tract estimates carry sampling error that is not propagated. `calculate_exposure_metrics` turns a facility's candidate stacks (all of them in one call, so the per-stack loop runs in code rather than in the model), the emission rate, the weather, the population and the toxicity values into a screening air concentration, dose per age band, hazard quotient and cancer risk for each stack, plus the range over the stacks with the stack behind each end, with the method of EPA's SCREEN3 model (EPA-454/B-95-004): the worst case is the highest ground-level concentration over its 54 combinations of stability class and 10 m wind speed and over distances from 100 m to 10 km (SCREEN3's own array continues to 50 km, but the Briggs dispersion coefficients in `models/transport/dispersion.py` are valid only to 10 km), with Briggs plume rise and stack-tip downwash, the wind-profile power law and the 1-hour to annual factor 0.08 (EPA-454/R-92-019). A `representative` result uses the weather of the meteorology tool. Exposure factors are the EPA RSL resident-air defaults and the age-band inhalation rates and body weights come from the 2011 Exposure Factors Handbook; every constant is in the `[exposure]` table with its source. Limits: flat terrain, rural dispersion, no building downwash and no mixing-height limit, so it can understate unstable-weather impacts; the maximum may be where nobody lives. Anything it cannot compute is null with a warning and nothing is defaulted. The agent's system prompt (`prompts/agent_system.md`) teaches how an exposure assessor reasons and names no tool; each tool's description says when it applies and how to read its results, and tests keep it that way. All tools are now implemented.

## Running the agent

The chat model is configured in one place, `[agent]` in `config/settings.toml` (provider, model,
API-key variable, timeout, step limit). The program and the evaluations both build it from there
with `app/chat_model.py`, so they always run the same model:

```bash
uv run python -m app "Assess CAS 71-43-2"
```

## Evaluating the agent

`uv run pytest -m eval` runs the agent with the `[agent]` model on the scenarios in
`evals/scenarios.py`, checks its tool calls in code, and scores its reply with an LLM judge
(`[evaluation].judge_model`) through Evidently; an HTML report is written to `evals/reports/`.
Network tools are replayed from `evals/cassettes/` (a missing recording fails closed). The
evaluations need `OPENAI_API_KEY`, cost tokens, and are excluded from the default `pytest` run.

```bash
uv run python -m evals run                     # all unblocked scenarios: PASS/FAIL + reasons
uv run python -m evals run chemical-name-only  # one scenario
uv run python -m evals record full-assessment-with-nei-stacks  # re-record from live services
```

Recording runs the scenario once against the live services (it needs the CompTox and Census
keys too) and saves every network tool output; never edit a cassette by hand. Reports land in
`evals/reports/<timestamp>/<scenario>.html`.

## Swapping the LLM provider

Change `[agent]` in `config/settings.toml` (a new provider is an entry in `app/chat_model.py`).
Underneath, `build_agent` accepts any `langchain_core.language_models.BaseChatModel` that supports tool calling. It never imports a provider, so you construct the model and inject it:

```python
from agent import build_agent

# OpenAI
from langchain_openai import ChatOpenAI

agent = build_agent(ChatOpenAI(model="gpt-4.1"))

# Anthropic
from langchain_anthropic import ChatAnthropic

agent = build_agent(ChatAnthropic(model="claude-sonnet-5-5"))

# Vertex AI
from langchain_google_vertexai import ChatVertexAI

agent = build_agent(ChatVertexAI(model="gemini-2.5-pro"))

agent.invoke({"messages": [("user", "Assess benzene (71-43-2) emissions")]})
```

Install the matching integration package yourself (e.g. `uv add langchain-anthropic`); none is a hard dependency.

## Adding a tool

0. Put any equations in `models/` first (pure functions with units in the docstring) and have the tool call them.
1. Add a typed `@tool` function in the matching concern folder (or a new folder), e.g. `tools/emissions/my_tool.py`. Put shared payload types in `tools/schemas.py`. Write a rich docstring (purpose, `Args:`, `Returns:`): the model reads it to decide when and how to call the tool.
2. Add it to the `TOOLS` list in that folder's `__init__.py`.
3. For a new folder, import its `TOOLS` in `tools/registry.py` and register it in `_build_default_registry`.
4. Add the tool name to `tests/tools/test_registry.py` and add a test in the matching `tests/tools/<concern>/` folder.

Tool names must be unique; the registry raises `ValueError` on duplicates.

## Development

    uv run pytest          # tests
    uv run ruff check .    # lint
    uv run ruff format .   # format
    uv run pyright         # strict type check
    uv run pre-commit install        # one-time: enable git hooks
    uv run pre-commit run --all-files

Pre-commit runs on every commit: file hygiene, ruff (lint + format), `uv lock` check, detect-secrets, strict pyright, bandit (security lint) and pytest. If detect-secrets flags a false positive, review it and update the baseline with `uv run detect-secrets scan > .secrets.baseline` (after checking the diff). Dependency CVEs: `uv run pip-audit`.
