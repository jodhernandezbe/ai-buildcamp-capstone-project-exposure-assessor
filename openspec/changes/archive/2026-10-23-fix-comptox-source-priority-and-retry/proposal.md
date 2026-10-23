## Why

Comparing CompTox's ToxVal records with EPA's IRIS endpoint showed two faults in how toxicity
values are fetched today:

- The configured source priority is `["IRIS"]`, but ToxVal names the source `"EPA IRIS: IRIS"`.
  The comparison is exact, so IRIS is never preferred: sources rank by order of appearance, and
  benzene's four values were reported as `Alaska DEC` although IRIS records exist (toluene's RfC
  too).
- A transient failure (a connection reset, HTTP 429/5xx, a timeout) is not retried, so the
  lookup returns nothing and the agent is told no benchmark exists. Formaldehyde and acrolein
  came back empty once and complete minutes later. An empty CompTox answer now also triggers the
  PubChem fallback.

## What Changes

- Set the shipped `source_priority` to the name the API reports, `"EPA IRIS: IRIS"`, and state
  in the spec that source names are those of the API.
- Retry CompTox requests on timeouts, connection errors, HTTP 429 and HTTP 5xx, a configured
  number of times with a doubling wait (`Retry-After` honoured), before giving up as today.
  Definitive answers (200, 404, 400 "found 0 results") are never retried.
- Add `max_retries` and `backoff_seconds` to `[comptox]`.
- Share the retryable-status set and `Retry-After` reader of `tools/http.py` instead of copying
  them.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `comptox-toxicity-lookup`: the source order names sources as the API reports them, and IRIS
  ranks first.
- `comptox-property-lookup`: transient failures are retried before the lookup gives up.

## Impact

- `config/settings.toml`, `config/loader.py` (two settings), `tools/http.py` (two names made
  public), `tools/informatics/helpers/comptox.py`.
- Behavior: values for chemicals whose first-listed source was not IRIS may change to the IRIS
  value, with source `EPA IRIS: IRIS`; fewer false "no data" results.
- Tests in `tests/tools/informatics/helpers/test_comptox.py`, `tests/config/test_loader.py`;
  agent evals re-run (cassettes replay tool outputs, so no re-recording is needed).
