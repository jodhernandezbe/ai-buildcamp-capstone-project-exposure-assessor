## ADDED Requirements

### Requirement: Tracts with distance and bearing
Besides the pooled count and age mix, the population tool SHALL return for each census tract that intersects the circle the tract's residents, its age mix as percent in the same four bands, its distance from the point (m) and its bearing from the point (degrees clockwise from north), both measured to the tract's internal point as the tract service reports it, and that point's latitude and longitude (decimal degrees) as reported. A tract with no usable estimate SHALL be left out of the list with a warning, as it is of the pooled count. The tract list SHALL be bounded by a configured maximum and say how many tracts were left out. The pooled count and age mix SHALL be unchanged.

#### Scenario: Tract list
- **WHEN** three tracts intersect the circle
- **THEN** each is returned with its residents, age mix, distance and bearing, and the pooled count equals what it was before

#### Scenario: Coordinates as reported
- **WHEN** a tract is listed
- **THEN** its latitude and longitude are the internal point the tract service gave, not a computed position

#### Scenario: Tract without an internal point
- **WHEN** a tract's internal point is missing
- **THEN** it is counted in the pooled result, left out of the list, and a warning says so

#### Scenario: Tract list is capped
- **WHEN** more tracts intersect the circle than the configured maximum
- **THEN** the nearest are returned and the result says how many were left out

#### Scenario: Screening default
- **WHEN** the screening default is used because the estimate could not be made
- **THEN** the tract list is empty and the default's reason is carried
