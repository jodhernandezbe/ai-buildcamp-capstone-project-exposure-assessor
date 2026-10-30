# operating-profile Specification

## Purpose

The operational profile of a facility: its operating schedule, TSCA life cycle stage, condition of use and CDR industrial sector, which the worker screening uses.

## Requirements

### Requirement: Schedule from the Census QPC baseline
The system SHALL derive a facility's schedule from the matched Census QPC hours per week: days per week from a configured shift length (hours per day, default 8, so days per week is the smaller of 7 and the hours per week over the shift length, rounded up), hours per day as hours per week over days per week, operating days per year as days per week times the configured weeks per year, and annual operating hours as the smaller of 8,760 and hours per week times weeks per year. The source SHALL name the QPC release and matched NAICS code and SHALL say that days per week is derived. With no match the schedule SHALL be the configured default schedule and the source SHALL say so.

#### Scenario: Two-shift plant
- **WHEN** the matched baseline is 80 hours per week and the shift length is 8
- **THEN** days per week is 7 (capped), hours per day is about 11.4 and annual hours is 80 x the configured weeks per year

#### Scenario: Single-shift plant
- **WHEN** the matched baseline is 40 hours per week
- **THEN** days per week is 5 and hours per day is 8

#### Scenario: Continuous operation
- **WHEN** the matched baseline is 168 hours per week and the weeks per year is 52.14
- **THEN** annual operating hours is 8,760

#### Scenario: No match
- **WHEN** no baseline row matches the facility's code
- **THEN** the configured default schedule is used and its source says so

#### Scenario: Invalid configuration
- **WHEN** the shift length or weeks per year is zero, negative or non-numeric
- **THEN** the settings loader raises a `ValueError`

### Requirement: CDR industrial sector from NAICS
The system SHALL give a facility's CDR industrial sector code (IS) and name from a version-controlled reference file mapping NAICS codes to the sectors of the EPA Chemical Data Reporting instructions, matching the facility's code by the longest prefix, and SHALL read and validate the file once per process. A code with no row SHALL give a null sector with the reason; the system SHALL NOT infer a sector from the title.

#### Scenario: Match
- **WHEN** the reference maps 3251 to a sector and the facility's code is 325199
- **THEN** that sector is returned with the matched prefix

#### Scenario: No match
- **WHEN** no prefix of the code is in the file
- **THEN** the sector is null and the reason says so

#### Scenario: Unreadable file
- **WHEN** the file is missing or malformed
- **THEN** every sector is null with one warning and the rest of the profile is unaffected

### Requirement: Life cycle stage and condition of use from the reported activities
The system SHALL give the facility's life cycle stages and conditions of use from the TRI Section 3 activities already mapped through the TSCA crosswalk, and SHALL NOT derive them from the NAICS code. When the facility reported no mappable activity they SHALL be empty with the existing note, and the profile SHALL still carry its schedule and sector.

#### Scenario: Reported activities
- **WHEN** the facility reported 3.2a
- **THEN** its stage and condition of use are those of the crosswalk row

#### Scenario: No activities
- **WHEN** the facility reported none
- **THEN** stage and condition of use are empty with the note, not defaulted to "Manufacturing"

### Requirement: Profile shape
The system SHALL return an operational profile with `naics_code`, `life_cycle_stage` (the distinct stages), `cou_category` (the distinct categories), `cdr_sector` (code and name, or null), `days_per_week`, `operating_days_per_year`, `hours_per_day`, `annual_operating_hours` and the sources and warnings behind them.

#### Scenario: Complete profile
- **WHEN** a facility has a baseline match, a sector and activities
- **THEN** every field is present with its sources

#### Scenario: Partial profile
- **WHEN** the sector is unknown
- **THEN** that field is null with a reason and the others are unaffected
