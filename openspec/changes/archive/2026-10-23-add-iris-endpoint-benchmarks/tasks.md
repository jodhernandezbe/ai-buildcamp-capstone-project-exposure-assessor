## 1. Configuration

- [x] 1.1 Add `[comptox.iris]` to `config/settings.toml`: `path`, the field entries for `rfd` and `rfc`, `agreement_tolerance`
- [x] 1.2 Add its typed loader to `config/loader.py` with validation and tests (negative cases)

## 2. Reading the endpoint

- [x] 2.1 `helpers/iris_text.py`: strict value reader; tests for plain, `a x 10 e`, refused shapes and unit handling
- [x] 2.2 Fetch the endpoint in `ComptoxLookup` (own definitive flag, cached like the rest, never raising)
- [x] 2.3 Turn the record into `ToxicityValue`s (route, systems as endpoint, non-cancer, revision)

## 3. Precedence and checks

- [x] 3.1 Place the endpoint value ahead of the ToxVal choice for `rfd` and `rfc` only
- [x] 3.2 Warn on disagreement with a ToxVal IRIS record beyond the tolerance
- [x] 3.3 Tests: precedence, no endpoint value, subchronic only, unreadable text, endpoint failure falls back to ToxVal, cancer values untouched

## 4. Verification

- [x] 4.1 Live check: formaldehyde RfC 0.007 mg/m3 from the endpoint, benzene values unchanged
- [x] 4.2 ruff, pyright, bandit, function length, pytest, frontend check, pre-commit
- [x] 4.3 Run the agent evaluations several times and compare with the same-day runs of the unchanged code
