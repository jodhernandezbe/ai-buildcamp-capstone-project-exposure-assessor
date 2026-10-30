## ADDED Requirements

### Requirement: Schedule beside the hours
The system SHALL return, with the operating hours per year of a facility, the schedule defined by the operating-profile capability (days per week, hours per day, operating days per year), from the same match, so the hours per year, the schedule and the source always agree.

#### Scenario: Same match
- **WHEN** a facility matches the 3252 row
- **THEN** its hours per year and its schedule both come from that row and the source names it

#### Scenario: Default
- **WHEN** no row matches
- **THEN** hours and schedule are the configured defaults and the source says so
