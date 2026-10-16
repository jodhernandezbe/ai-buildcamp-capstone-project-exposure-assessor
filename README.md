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
    models/                  pure NumPy physics, no LLM/LangChain imports
      dispersion.py          Pasquill-Gifford sigmas, Gaussian plume
      dose.py                ADD, LADD
      risk.py                emission rate, hazard quotient, cancer risk
    prompts/
      registry.py            load_prompt(name) reads prompts/<name>.md
      agent_system.md        system prompt (XML-tagged sections)
    tools/
      registry.py            ToolRegistry + ALL_TOOLS / get_all_tools()
      schemas.py             TypedDicts shared by tool inputs/outputs
      informatics/properties.py   fetch_chemical_properties
      emissions/inventory.py      query_emissions_inventory
      emissions/stack.py          fetch_stack_parameters
      geospatial/metadata.py      get_facility_metadata
      exposure/meteorology.py     get_meteorological_boundary
      exposure/metrics.py         get_population_receptors, calculate_exposure_metrics
    tests/                   pytest suite, mirrors the package layout

The intended tool flow for an assessment: chemical properties -> emissions inventory -> facility metadata -> stack parameters -> meteorology and population -> exposure metrics. `fetch_chemical_properties` is implemented (CAS -> SMILES -> CompTox, with Pint unit conversion to fixed units), and so is `query_emissions_inventory` (CAS -> EPA TRI facilities with their latest reported stack-air release, location and an average emission rate in g/s at 8760 operating hours per year, configurable in `config/settings.toml`); the other tools are stubs that raise `NotImplementedError`.

## Swapping the LLM provider

`build_agent` accepts any `langchain_core.language_models.BaseChatModel` that supports tool calling. It never imports a provider, so you construct the model and inject it:

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
