## MODIFIED Requirements

### Requirement: Resilient to service failures
The system SHALL return no properties, rather than raise, when CompTox is unreachable, times out, or answers with an error status or malformed body. Before giving up it SHALL retry a timed-out, connection-failed, throttled (HTTP 429) or server-error (HTTP 5xx) request the configured number of times, waiting a configured time that doubles on each retry (and the service's `Retry-After`, up to the request timeout, when given). A definitive "no match" answer (an empty result, HTTP 404, or HTTP 400 stating that zero results were found) MAY be cached and SHALL NOT be retried; transient failures SHALL NOT be cached.

#### Scenario: Network failure
- **WHEN** a request fails or times out on every attempt
- **THEN** no properties are returned and a later call for the same input contacts CompTox again

#### Scenario: Repeat lookup
- **WHEN** the same CAS number is looked up again after a successful lookup
- **THEN** the cached result is returned without contacting CompTox

#### Scenario: Zero-results answer
- **WHEN** CompTox answers HTTP 400 stating that zero results were found for the CAS number
- **THEN** it is treated as "no match", not as a transient failure, and is not retried

#### Scenario: Transient failure then success
- **WHEN** a request fails with a connection error or HTTP 429, 500, 502, 503 or 504 and the next attempt succeeds
- **THEN** the lookup returns the values of the successful attempt

#### Scenario: Retries exhausted
- **WHEN** every attempt fails transiently
- **THEN** exactly one more request than the configured retries is made, no properties are returned, and nothing is cached

#### Scenario: Not found is final
- **WHEN** CompTox answers HTTP 404
- **THEN** the request is not retried

#### Scenario: Waiting between attempts
- **WHEN** a request is retried
- **THEN** the wait is the configured backoff doubled per retry, or the service's `Retry-After` capped at the request timeout
