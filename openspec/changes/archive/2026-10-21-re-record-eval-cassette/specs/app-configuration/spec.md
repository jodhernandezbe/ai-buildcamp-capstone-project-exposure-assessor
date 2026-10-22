## ADDED Requirements

### Requirement: CompTox certificate waiver setting
The `[comptox]` table SHALL carry `accept_expired_certificate`, a boolean, validated on load, with a comment saying it is for a lapse of the service's certificate and is to be turned off again.

#### Scenario: Not a boolean
- **WHEN** the value is missing or not a boolean
- **THEN** the loader raises a `ValueError` naming the key
