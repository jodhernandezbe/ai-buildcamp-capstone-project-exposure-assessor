# tri-conditions-of-use Specification

## Purpose
Derives a facility's TSCA life cycle stages and conditions of use from the Section 3 activities it reports to TRI, read in the same release query without duplicating rows and mapped through the EPA crosswalk, never guessing.

## Requirements
### Requirement: Activities come with the release query, without duplicate rows
The TRI release request SHALL also join the `tri_chem_activity` table on the submission's control number, so each row carries the submission's Section 3 activity flags in the same request, and SHALL NOT make a request per facility or per submission. The join SHALL NOT change which rows or how many rows come back, and no release SHALL be counted more than once because of it. Activities SHALL be kept as a set per facility, so a repeated row leaves a facility's conditions unchanged.

#### Scenario: Same rows with and without the join
- **WHEN** the inventory of a chemical is read with and without the activity join
- **THEN** the same facilities are returned with the same releases

#### Scenario: Repeated rows
- **WHEN** the same submission's rows come back more than once (for example once per NAICS code)
- **THEN** the facility's conditions of use contain each condition once

#### Scenario: One request
- **WHEN** a lookup returns many facilities
- **THEN** no request beyond the paged release query is made for activities

### Requirement: Activity flags read fail-closed
The system SHALL read the activity flags named in the configuration (flag column to Form R section) and treat a flag as set only when it is the number 1 or the text "1". A flag that is 0, null, absent, boolean, or any other value SHALL NOT set the activity.

#### Scenario: Set flags
- **WHEN** a row has `reactant` "1" and `produce` 0
- **THEN** the activities are Section 3.2a only

#### Scenario: Unusable values
- **WHEN** a flag is null, "yes", true, 2 or missing
- **THEN** that activity is not set

### Requirement: Facility activities are those of its latest-year submissions
A facility's activities SHALL be the union of the activities of all the reports that make up its latest-year release (the reports whose quantities are added together). A report of an earlier year SHALL NOT contribute, and when a later year replaces an earlier one the earlier year's activities are discarded.

#### Scenario: Two reports in the latest year
- **WHEN** two submissions of the latest year report 3.2a and 3.2b respectively
- **THEN** the facility has both activities

#### Scenario: Older year
- **WHEN** an earlier year's report has activity 3.1a and the latest year's has none set
- **THEN** the facility does not have 3.1a

### Requirement: Mapping through the crosswalk
The system SHALL map each activity to rows of the configured crosswalk CSV by Form R section, using only rows of the configured mapping level (`1_lifecycle_stage`) that name no TRI sub-use code, and SHALL produce, for each matching row, a condition of use with the TRI activity, the Form R section, the TSCA life cycle stage, the TSCA COU category and the mapping strength, exactly as the crosswalk states them. An activity with several matching rows SHALL give several conditions. Conditions SHALL be distinct and ordered by Form R section, then crosswalk order. The distinct life cycle stages SHALL be listed in that order.

#### Scenario: One-to-one
- **WHEN** a facility reports only 3.2a
- **THEN** it has one condition: Processing, "Processing as a reactant", strength Direct

#### Scenario: One activity, two conditions
- **WHEN** a facility reports 3.3c and the crosswalk has two rows for it (Industrial use and Commercial use)
- **THEN** it has two conditions for that activity and both stages are listed

#### Scenario: Several activities
- **WHEN** a facility reports 3.1a, 3.2b and 3.3c
- **THEN** its conditions cover Manufacturing, Processing and the stages of 3.3c, with each stage listed once

#### Scenario: Finer rows ignored
- **WHEN** the crosswalk also has CDR function-code or sub-use rows for the same section
- **THEN** they are not used

### Requirement: Nothing is guessed
An activity whose section has no matching crosswalk row SHALL be left out and counted in a warning. An impurity activity whose crosswalk strength states that CDR exempts it SHALL still be returned, with that strength, so that the reader can see the activity is not a condition of use in the CDR sense. When no activity is set, or the submission returned no activity columns, `conditions_of_use` and `lifecycle_stages` SHALL be empty and `conditions_note` SHALL say which of the two applies; otherwise `conditions_note` SHALL be null.

#### Scenario: Unmapped activity
- **WHEN** a configured flag's section is not in the crosswalk
- **THEN** that activity gives no condition and a warning counts it

#### Scenario: Impurity
- **WHEN** a facility reports 3.2e (process impurity)
- **THEN** it has a condition with category "Not a COU category (process impurity)" and strength "None (CDR exempt)"

#### Scenario: No activity reported
- **WHEN** every flag is 0
- **THEN** the lists are empty and the note says TRI reported no activity

#### Scenario: Columns missing
- **WHEN** the rows carry no activity columns at all
- **THEN** the lists are empty and the note says the activity data was not returned

### Requirement: Crosswalk is validated once and read once
The system SHALL read the crosswalk file once per process, check that every configured column exists, and ignore rows with an empty section, stage or category. A missing file or column SHALL make the conditions unavailable for the run, with one warning and a `conditions_note` on every record, and SHALL NOT fail the inventory.

#### Scenario: Missing file
- **WHEN** the crosswalk file does not exist
- **THEN** the inventory is returned without conditions, each record's note says so, and one warning names the file

#### Scenario: Missing column
- **WHEN** a configured column is not in the file
- **THEN** the same as for a missing file

### Requirement: Configuration, not code
The system SHALL read the crosswalk path, its column names, the mapping level, the flag-to-section table and the activity labels from a typed `[conditions_of_use]` section of `config/settings.toml`, validated on load with errors naming the key, and SHALL read the join in the release query path from `[tri]`.

#### Scenario: Another flag
- **WHEN** a flag is added to the table with its section
- **THEN** it is read and mapped with no code change

#### Scenario: Invalid setting
- **WHEN** a section is empty, a flag column is repeated, or the level is empty
- **THEN** loading fails with an error naming the key
