# pubchem-request-policy Specification

## Purpose
Keeps calls to PubChem within its usage policy and avoids repeating them, so the agent and its tests are good citizens of a shared public service.

## Requirements

### Requirement: Stay within the PubChem rate limit
The system SHALL make no more than 5 requests per second to PubChem, counting retries, and SHALL send a descriptive `User-Agent` that identifies the application. A request SHALL always have a timeout.

#### Scenario: Consecutive requests
- **WHEN** several requests are made in a row
- **THEN** each waits at least the configured delay, which is at least 0.2 seconds, before it is sent

#### Scenario: Delay below the limit
- **WHEN** the configured delay is shorter than 0.2 seconds
- **THEN** loading the configuration fails with a message naming the PubChem limit

#### Scenario: Request is identifiable
- **WHEN** a request is sent
- **THEN** it carries a `User-Agent` naming the application

#### Scenario: PubChem is slow
- **WHEN** PubChem does not answer within the configured timeout
- **THEN** the request is abandoned and counted as a failed attempt

### Requirement: Back off when PubChem asks
The system SHALL retry a throttled (HTTP 429, with PubChem's `Retry-After` honoured), busy (HTTP 503) or timed-out request a configured number of times with a growing wait, and then give up with a reason. It SHALL NOT retry other errors.

#### Scenario: Throttled once
- **WHEN** the first answer is HTTP 429 and the second is a success
- **THEN** the success is returned

#### Scenario: Still failing
- **WHEN** every attempt fails
- **THEN** the lookup gives up with a reason after the configured number of retries

#### Scenario: Not found is final
- **WHEN** PubChem answers HTTP 404
- **THEN** the request is not retried

### Requirement: Cache answers on disk
The system SHALL keep a local cache of PubChem answers, keyed by the full request URL, so a repeated request is answered without calling PubChem. The system SHALL cache successful answers and definitive "not found" answers, and SHALL NOT cache failures (timeouts, throttling, server errors, malformed JSON). An entry older than the configured lifetime SHALL be ignored and replaced. A cache that is unreadable, corrupt or not writable SHALL NOT stop a lookup: the system SHALL log a warning and call PubChem.

#### Scenario: Repeated request
- **WHEN** the same URL is requested twice within the lifetime
- **THEN** PubChem is called once

#### Scenario: Cached not-found
- **WHEN** a name was answered 404 and is requested again
- **THEN** it is answered "not found" from the cache without a request

#### Scenario: Failure not cached
- **WHEN** a request fails with a server error and is then repeated
- **THEN** the second attempt calls PubChem

#### Scenario: Expired entry
- **WHEN** an entry is older than the configured lifetime
- **THEN** PubChem is called and the entry is replaced

#### Scenario: Broken cache
- **WHEN** the cache file is corrupt or its directory is not writable
- **THEN** the lookup still succeeds from PubChem and a warning is logged

#### Scenario: Cache disabled
- **WHEN** the configuration disables the cache
- **THEN** every request goes to PubChem and no file is created

### Requirement: Configure every PubChem setting
The system SHALL read the URL templates, the section headings, the delay, timeout, retries, backoff, user agent and the cache location and lifetime from configuration, validated when loaded.

#### Scenario: Invalid value
- **WHEN** a URL template lacks its placeholder, or a delay, timeout or lifetime is not a positive finite number
- **THEN** loading the configuration fails with a message naming the setting
