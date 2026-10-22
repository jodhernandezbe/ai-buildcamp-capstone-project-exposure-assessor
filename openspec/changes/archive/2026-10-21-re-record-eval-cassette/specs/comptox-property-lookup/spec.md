## ADDED Requirements

### Requirement: Certificate verification waives the dates only, by setting
The CompTox client SHALL verify the service's TLS certificate fully by default. When the `accept_expired_certificate` setting is on, it SHALL skip only the certificate's validity-dates check: the chain SHALL still be validated against the trusted roots and the host name SHALL still be checked. Verification SHALL never be turned off, and the API key SHALL never be sent over an unverified connection.

#### Scenario: Default
- **WHEN** the setting is off
- **THEN** the client verifies the certificate fully

#### Scenario: Lapsed certificate accepted
- **WHEN** the setting is on and the service's certificate has expired but is otherwise valid for the host
- **THEN** the request succeeds

#### Scenario: Wrong host or untrusted chain
- **WHEN** the setting is on and the certificate is for another host or not signed by a trusted root
- **THEN** the request fails
