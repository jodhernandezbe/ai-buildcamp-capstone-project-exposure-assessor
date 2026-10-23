## 1. Source priority

- [x] 1.1 Set `source_priority = ["EPA IRIS: IRIS"]` in `config/settings.toml` and correct its comment
- [x] 1.2 Tests: the shipped value, and an IRIS record winning over an earlier-listed other source using the shipped name

## 2. Retry

- [x] 2.1 Make `RETRYABLE_STATUS` and `retry_after` public in `tools/http.py` and use them there
- [x] 2.2 Add `max_retries` and `backoff_seconds` to `[comptox]`, `ComptoxSettings` and its loader; update the settings tests and the test settings in `test_comptox.py`
- [x] 2.3 Retry loop in `ComptoxLookup` as designed
- [x] 2.4 Tests: connection error then success, 429/503 then success, exhausted retries (count, nothing cached, later call retries), 404 and 400 zero-results not retried, waits (backoff doubling, `Retry-After` capped)

## 3. Verification

- [x] 3.1 ruff, pyright, bandit, function length, pytest, frontend check, pre-commit
- [x] 3.2 Run `uv run pytest -m eval` three times; compare with the earlier runs
- [x] 3.3 Live check: benzene's four values report `EPA IRIS: IRIS`
