## ADDED Requirements

### Requirement: Concentration at a stated distance for a fixed scenario
The model SHALL give the 1-hour ground-level centerline concentration (ug/m^3) at a stated downwind distance (m) for a scenario's emission rate, stability class, wind speed and stack, using the same dispersion and plume rise as the worst-case search; the annual average follows by the same factor as for the maximum. At the distance of the worst-case maximum it SHALL equal that maximum, and it SHALL NOT exceed it at any other distance.

#### Scenario: At the maximum
- **WHEN** the distance is the one of the worst-case maximum
- **THEN** the concentration equals the maximum

#### Scenario: Elsewhere
- **WHEN** the distance is smaller or larger than the one of the maximum
- **THEN** the concentration is not larger than the maximum

#### Scenario: Invalid input
- **WHEN** the distance is not finite or outside 100 to 10,000 m
- **THEN** the model raises rather than returning a number
