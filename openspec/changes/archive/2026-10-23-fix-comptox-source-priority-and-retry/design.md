## Context

See proposal.md. `ComptoxLookup._get_json` makes one request and maps any failure to
"not definitive". `tools/http.py` already has the retry vocabulary (`_RETRYABLE_STATUS`,
`_retry_after`) used by `RetryingClient`, which cannot be used here because it discards the
response body, and the CompTox client needs it to recognise HTTP 400 "found 0 results".

## Decisions

- **Source name:** change the configured value to `"EPA IRIS: IRIS"` (the exact string the API
  returns, seen in ToxVal records). Ranking code and the "unlisted sources" rule are unchanged.
  Alternative: match by substring or prefix; rejected, since a loose match could silently pick
  an unintended source. A test pins the shipped value to the API's name.
- **Retry loop inside `_get_json`:** `_request` repeats the GET up to `max_retries + 1` times
  while the outcome is an `httpx.HTTPError` or a status in the shared retryable set; it sleeps
  the configured delay before every attempt (as today) and, between attempts, a wait of
  `backoff_seconds * 2**attempt` or `Retry-After` capped at `timeout_seconds`. The last
  response (or none) goes to the existing `_parse`, so every failure stays "not definitive" and
  nothing new is cached.
- **Share, do not copy:** `tools/http.py` makes `RETRYABLE_STATUS` and `retry_after` public.
- **Settings:** `max_retries` (default shipped: 2) and `backoff_seconds` (2.0) under `[comptox]`;
  the loader requires them. The delay before each request still applies, so the request rate is
  not higher than before the first attempt.

## Risks / Trade-offs

- [Longer worst-case time when CompTox is down: delay + timeout per attempt, three attempts,
  per request] → timeout stays 15 s; `max_retries` is configuration.
- [Preferring IRIS changes some reported values and sources] → intended: IRIS is the
  established reference; values equal the previous ones for the chemicals checked (benzene,
  hexane, toluene, naphthalene, DBCP, acrolein), only the source label differs there.
