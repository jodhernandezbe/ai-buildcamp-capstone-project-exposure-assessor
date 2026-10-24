## 1. Configuration and units

- [ ] 1.1 Add per-quantity accepted-unit lists and plausible ranges for chemistry quantities (vapor pressure, molecular weight, density, RfD, RfC, SF, IUR) to `config/settings.toml`, with typed loading in `config/`
- [ ] 1.2 Add the accepted-unit lists for stack parameters (height, diameter, exit velocity, exit temperature) beside the existing `[stack.ranges]`
- [ ] 1.3 Add a validator for an entered value: finite number, not a boolean, exact conversion through `commons/units.convert`, inside the plausible range; temperature converted as an absolute temperature
- [ ] 1.4 Unit tests: unit conversions (torr to mmHg, ft to m, degC to K), reciprocal IUR units, rejected values (NaN, bool, text, out of range, wrong quantity) each with a negative test

## 2. Pending request in the agent

- [ ] 2.1 Define the typed request record (request id, thread, entries with field, subject, accepted units, plausible range, purpose) in `tools/schemas.py`
- [ ] 2.2 Add the missing-value check that reads tool warnings and nulls for the requested result and builds the request (a small function, no decisions about the result)
- [ ] 2.3 Add a stop-and-ask step to the graph: the turn ends after the model writes the request, with the request stored in thread state
- [ ] 2.4 Inject accepted values into tool calls from thread state through the tool's config port, and add a short system note listing them, generated from state
- [ ] 2.5 Tests: request built only for values that change the requested result; one request for several values; declined values stay absent with their reason

## 3. Tools accept user-provided values

- [ ] 3.1 `fetch_chemical_properties` and `lookup_chemical_properties`: accept a supplied value for a field that is missing, label it "user-provided", never replace a found value
- [ ] 3.2 Stack parameter tools: accept supplied stack height, diameter, exit velocity and exit temperature for a missing one; set `stack_source` to "user-provided"
- [ ] 3.3 Tests for each tool, including "found value is kept" and "declined value stays None with its warning"
- [ ] 3.4 Confirm the tool descriptions do not change (the chemical-properties spec forbids mentioning other sources in the model-facing description); update `tests/tools/test_tool_descriptions.py` only if a new argument requires it

## 4. Chat contract and server

- [ ] 4.1 Add the confirmation request event to `api/schemas/chat.py` and the reply form (answers naming the request id) to `ChatRequest`
- [ ] 4.2 Server-side validation of answers against the open request: closed request, other thread, unlisted entry and out-of-range value each rejected without changing the thread
- [ ] 4.3 Thread handling: keep the open request across reloads (snapshot includes it); a new message closes open entries as proceed without and the agent says so
- [ ] 4.4 Regenerate `frontend/src/types/schema.json` and `frontend/src/types/api.ts`; run the contract test
- [ ] 4.5 API tests: valid answers start the next turn; answers for a closed request rejected; a server rejection of a browser-valid value

## 5. Frontend card

- [ ] 5.1 Add a confirmation card component in `frontend/src/features/chat/` with one row per entry: numeric input, unit selector, target unit label, Confirm and Proceed without
- [ ] 5.2 Browser-side validation mirroring the server rules for convenience; show the server's reason when it rejects
- [ ] 5.3 Render the card from the stream event and from the reloaded snapshot; hide it once answered
- [ ] 5.4 Component tests in the style of the existing chat tests (`ClearChatButton.test.tsx`, `MessageStream.test.tsx`)

## 6. Prompt

- [ ] 6.1 Add the missing-value reasoning to `prompts/agent_system.md` as assessment reasoning: ask once, in one message, only for values that change the result; no tool names or call order
- [ ] 6.2 Update `tests/prompts/test_agent_system.py` to check the new rule and that it names no tool

## 7. Evaluation

- [ ] 7.1 Add an evaluation scenario where a needed RfC is missing: the expected behaviour is a request, not a figure
- [ ] 7.2 Record the cassette for the confirmation turn and the answered follow-up turn
- [ ] 7.3 Run `uv run pytest -m eval` three times (project memory: single runs are not enough for prompt changes)

## 8. Quality gates

- [ ] 8.1 `uv run ruff format .` and `uv run ruff check .`
- [ ] 8.2 `uv run pyright`
- [ ] 8.3 `uv run bandit -c pyproject.toml -r agent app api commons config evals models prompts tools`
- [ ] 8.4 `uv run python scripts/check_function_length.py --max 18` over the source packages
- [ ] 8.5 `uv run pytest`
- [ ] 8.6 `npm --prefix frontend run check`
- [ ] 8.7 `uv run pre-commit run --all-files`, with no `--no-verify`
