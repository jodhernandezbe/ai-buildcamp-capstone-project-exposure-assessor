## ADDED Requirements

### Requirement: Distance and bearing between two points
The model SHALL give the great-circle distance (m) and the initial bearing (degrees clockwise from north, in [0, 360)) from a facility to a tract's internal point, given latitudes and longitudes in degrees, with a documented Earth radius.

#### Scenario: Due east
- **WHEN** the tract lies due east of the facility at the same latitude
- **THEN** the bearing is 90 degrees and the distance is the great-circle distance

#### Scenario: Same point
- **WHEN** the tract's point is the facility's
- **THEN** the distance is 0 m and the bearing is 0 degrees

#### Scenario: Invalid coordinates
- **WHEN** a latitude is outside [-90, 90] or a value is not finite
- **THEN** the model raises rather than returning a number
