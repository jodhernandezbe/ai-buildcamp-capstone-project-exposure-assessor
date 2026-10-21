## MODIFIED Requirements

### Requirement: Authenticated requests
The system SHALL send the CompTox API key with every request, and SHALL NOT store the key in code or configuration files. The key SHALL be the one made available to the current request when there is one (the web program supplies the key stored in the OS keychain for the duration of a turn), and otherwise the one read from the configured environment variable. The key SHALL be resolved afresh for every request and not held by the client between requests.

#### Scenario: Key available
- **WHEN** the configured environment variable is set and no request key is available
- **THEN** its value is sent in the configured API-key header

#### Scenario: Request key preferred
- **WHEN** a request key is available and the environment variable is also set
- **THEN** the request key is sent in the configured API-key header

#### Scenario: Key missing
- **WHEN** no request key is available and the configured environment variable is unset or blank
- **THEN** the system raises an error naming the variable, without contacting CompTox

#### Scenario: Key not retained
- **WHEN** a request has been made under one request key and a later one under another
- **THEN** each request sends its own key
