# eis-facility-lookup Specification

## Purpose

Resolves the EIS (Emissions Inventory System) identifier that the NEI uses for a facility from its FRS ID.

## Requirements


### Requirement: FRS ID to EIS ID
The system SHALL provide a helper that, given an FRS ID, queries the Envirofacts `FRS_PROGRAM_FACILITY` table for that registry ID and the EIS program and returns the distinct EIS facility IDs (`pgm_sys_id`) in response order. Rows whose registry ID differs from the one requested or whose program is not EIS SHALL be ignored. The path template, program name and field names SHALL come from the `[frs]` configuration.

#### Scenario: One EIS row
- **WHEN** the response holds one EIS row for the FRS ID
- **THEN** its `pgm_sys_id` is returned

#### Scenario: Several rows
- **WHEN** the response holds several rows with the same or different `pgm_sys_id`
- **THEN** the distinct IDs are returned in order

#### Scenario: No EIS registration
- **WHEN** the response is an empty list
- **THEN** no IDs are returned and the reason is reported as a warning

#### Scenario: Mismatched rows
- **WHEN** a row has another registry ID, another program, or no `pgm_sys_id`
- **THEN** it is ignored

#### Scenario: Request failure
- **WHEN** the request fails after its retries or returns an unexpected shape
- **THEN** no IDs are returned and the failure is reported as a warning (the lookup does not raise)

### Requirement: Validate the FRS ID before querying
The system SHALL accept the FRS ID as text (surrounding whitespace removed) or a non-negative integer, require digits only, and SHALL NOT send a request for a blank or non-digit value.

#### Scenario: Invalid FRS ID
- **WHEN** the FRS ID is blank, a boolean, negative, or contains non-digit characters
- **THEN** no request is made and no IDs are returned, with a warning
