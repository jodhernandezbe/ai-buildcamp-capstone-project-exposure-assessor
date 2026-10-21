## MODIFIED Requirements

### Requirement: Census API key handling
The system SHALL send the Census API key with every Census Data API request, and SHALL NOT embed, log or return it. The key SHALL be the one made available to the current request when there is one (the web program supplies the key stored in the OS keychain for the duration of a turn), and otherwise the one in the environment variable named in the configuration. When neither is available it SHALL make no Census Data API request and SHALL return the screening default with a warning that names the variable. When the service rejects the key (it answers with a redirect to a missing-key page or an authorization error) the warning SHALL say the key was rejected.

#### Scenario: No key configured
- **WHEN** no request key is available and the variable is not set
- **THEN** no Census Data API request is made and the screening default is returned with a warning naming the variable

#### Scenario: Request key preferred
- **WHEN** a request key is available and the environment variable is also set
- **THEN** the Census Data API request carries the request key

#### Scenario: Key rejected
- **WHEN** the service redirects to its missing-key page
- **THEN** the screening default is returned with a warning that the key was missing or rejected, and the request is not retried
