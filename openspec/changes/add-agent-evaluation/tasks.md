## 1. Setup and configuration

- [x] 1.1 Add `evidently` (pinned compatible range) with `uv add`; add the `eval` pytest marker and change `addopts` to `-m "not smoke and not eval"`
- [x] 1.2 `[evaluation]` in `config/settings.toml` and `config/evaluation.py` (frozen dataclass, validation, project-relative paths); tests with a negative case per key
- [x] 1.3 `evals/` package with `evals/CLAUDE.md`; add `evals` to the function-length, pyright and bandit gates (pre-commit, root `CLAUDE.md` commands and layout); ignore the reports directory in `.gitignore`

- [x] 1.4 `[agent]` settings and `config/agent.py` (provider, model, key variable, timeout, step limit) with tests; `[evaluation]` keeps only the judge, live tools and paths
- [x] 1.5 `app/` package: `chat_model.py` (the one chat model factory), `run.py` and `__main__.py` (`uv run python -m app "<question>"`), `app/CLAUDE.md`, gates and docs; evals build the agent model through it; tests with a fake environment and a fake model

## 2. Harness

- [ ] 2.1 `evals/cassette.py`: canonical argument key, replay tools that keep the production name/description/schema, fail-closed miss with unrecorded log, pass-through of live tools, recording wrapper and save; unit tests (hit, miss, live tool, int/str argument match, round trip) — replay and fail-closed miss done; recording wrapper and unit tests pending
- [ ] 2.2 `evals/runner.py`: build the OpenAI chat model from settings, build the agent with the given tools, invoke with the step limit, catch expected errors, extract the ordered call list and final report into a `RunRecord`; unit tests with a scripted fake chat model (completed run, error run, call/output pairing) — implemented; unit tests pending
- [ ] 2.3 `evals/checks.py`: `CheckResult` and composable check factories (completed, no unrecorded, called with arguments, not called, once per facility, once per NEI candidate, no fallback for facilities with candidates); unit tests incl. a failing case per check
- [ ] 2.4 `evals/judges.py` and `evals/scoring.py`: Evidently adapter (records → dataset, check descriptors with tests, OpenAI binary judges with reasoning, test summary, HTML report); unit test of the adapter with deterministic checks only — OpenAI binary judges with reasoning and HTML report done (judges live in `scoring.py`); check descriptors, test summary and unit test pending

## 3. Scenarios

- [x] 3.1 `evals/scenarios.py`: `Scenario` dataclass and catalogue; brainstormed scenarios listed, unimplemented ones marked blocked with a reason
- [ ] 3.2 `evals/__main__.py`: `record <scenario>` and `run` commands
- [ ] 3.3 Choose the chemical (few TRI facilities with NEI stacks), record the `full-assessment-with-nei-stacks` cassette from live services — chemical chosen: CAS 96-12-8 (two facilities, 5 and 10 NEI stacks); recording pending
- [x] 3.4 `tests/evals/conftest.py` (load `.env`, skip without key)
- [x] 3.5 Scenario `chemical-name-only` as a pytest test (`tests/evals/test_chemical_name_only.py`): run completes, no tool called, no CAS number in the reply
- [x] 3.6 LLM-judge test (OpenAI judge through Evidently): the reply asks for the CAS number and presents no results; reasoning in the failure message and the HTML report
- [ ] 3.7 `full-assessment-with-nei-stacks` scenario test (needs 2.3 and 3.3)

## 4. Gates

- [ ] 4.1 README: how to record and run evaluations
- [x] 4.2 ruff, pyright, bandit, function length, pytest, pre-commit all pass
- [x] 4.3 `openspec validate add-agent-evaluation --strict` passes
