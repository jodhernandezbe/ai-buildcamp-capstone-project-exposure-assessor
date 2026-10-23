## ADDED Requirements

### Requirement: Source names are those of the API, with IRIS first
The configured source order SHALL name sources exactly as the ToxVal API reports them in the `source` field (for IRIS, `EPA IRIS: IRIS`), and the shipped configuration SHALL rank EPA IRIS first.

#### Scenario: IRIS and another source both match
- **WHEN** a chemical has matching records from `EPA IRIS: IRIS` and from another source that appears earlier in the response
- **THEN** the IRIS record is used and its source is reported as `EPA IRIS: IRIS`

#### Scenario: Shipped order
- **WHEN** the shipped configuration is loaded
- **THEN** its first source is `EPA IRIS: IRIS`
