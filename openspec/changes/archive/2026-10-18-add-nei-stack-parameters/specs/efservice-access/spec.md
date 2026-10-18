## Purpose

One shared, polite client for EPA Envirofacts (`efservice`) requests, used by every tool that queries it.

## ADDED Requirements

### Requirement: Shared Envirofacts client
The system SHALL make every Envirofacts request through one client that waits the configured delay before each request, bounds each request by the configured timeout, retries HTTP 429, HTTP 5xx and timeouts a configured number of times with increasing waits (honouring `Retry-After` up to the timeout), and accepts only a JSON list of objects as a result. Any other failure SHALL raise an error naming the cause; no partial result SHALL be returned.

#### Scenario: Throttled then succeeds
- **WHEN** a request returns HTTP 429 and a later attempt succeeds
- **THEN** the rows of the successful attempt are returned

#### Scenario: Retries exhausted
- **WHEN** every attempt fails with a retryable error
- **THEN** an error naming the number of attempts and the last cause is raised

#### Scenario: Unexpected shape
- **WHEN** the response is not a JSON list of objects
- **THEN** an error is raised and the response is not used

### Requirement: Shared request settings
The Envirofacts base URL, delay between requests, request timeout, maximum retries and retry backoff SHALL be configured once, in an `[efservice]` table, and SHALL NOT be repeated per query or embedded in code.

#### Scenario: One change, all queries
- **WHEN** the configured delay is changed
- **THEN** both the TRI and the FRS queries use it
