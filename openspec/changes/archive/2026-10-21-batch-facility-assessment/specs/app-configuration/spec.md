## ADDED Requirements

### Requirement: Assessment settings
The system SHALL read from an `[assessment]` table the most facilities fully assessed per call, the most refined with their own stacks per call, the number processed at a time, the SCC similarity floor (greater than 0, at most 1), the most PSTK stacks per facility, how long an inventory is reused (seconds, zero or more), the most worst-case-only facilities listed to the model, and the reanalysis grid cell (degrees, greater than 0) within which facilities share the weather; and from `[assessment.screening]` the HQ threshold and the cancer-risk threshold (both greater than 0) and the screening ambient temperatures (a non-empty list of positive kelvin values), validated on load.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the assessment settings
- **THEN** it returns the values from the file

#### Scenario: Invalid entry
- **WHEN** a count is not a positive integer or is a boolean, the floor is not in (0, 1], the reuse time is negative, a threshold or the cell is not positive, or the temperatures are empty or not all positive numbers
- **THEN** the loader raises a `ValueError` naming the key

### Requirement: EIS lookup settings for many facilities
The `[frs_eis]` table SHALL also give the number of same-site searches run at a time (a positive integer) and how long a facility's EIS IDs are reused (seconds, zero or more), validated on load.

#### Scenario: Invalid entry
- **WHEN** the number of searches is not a positive integer or the reuse time is negative
- **THEN** the loader raises a `ValueError` naming the key
