## ADDED Requirements

### Requirement: NEI stack file settings
The system SHALL read the location of the NEI release-point file, the column holding the facility FRS ID, the columns holding stack height, stack diameter, exit velocity and exit temperature, and the unit each of those columns is reported in from the configuration file, and SHALL NOT embed them in Python code. Plausible ranges and target units SHALL be the ones already configured for stack parameters. A relative path SHALL be resolved against the project root.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the stack settings
- **THEN** it returns the NEI file path, FRS ID column, the four value columns and their reported units

#### Scenario: Changing a column or unit
- **WHEN** a column name or reported unit in the NEI table is edited
- **THEN** subsequent lookups use it with no code change

#### Scenario: Invalid NEI entry
- **WHEN** the NEI table lacks the path, the FRS ID column, any value column or any unit, or a unit is not a string
- **THEN** the loader raises a `ValueError` naming the offending key
