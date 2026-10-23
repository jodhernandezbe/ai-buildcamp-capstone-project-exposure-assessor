# naics-subsectors Specification

## Purpose
Gives each facility its three-digit NAICS subsector and that subsector's title from a local table built from the Census code lists, so the dashboard can group facilities by industry.

## Requirements
### Requirement: Local table of subsector titles
The system SHALL keep a local table of 3-digit NAICS subsector codes and titles (`data/naics_subsectors.csv`: code, title, vintage), built by a developer script from the Census Bureau's 2-6 digit code workbooks of the NAICS vintages in use (newest title wins, the row says its vintage), with Unix line endings and one row per code so that the build is reproducible. The script SHALL find the code and title columns by their headers, not by position, because those workbooks carry a leading sequence-number column, and SHALL keep only rows whose code is exactly three ASCII digits.

#### Scenario: Newest vintage wins
- **WHEN** a subsector appears in the 2017 and 2022 workbooks with different titles
- **THEN** the table has one row with the 2022 title and vintage 2022

#### Scenario: Older-only code
- **WHEN** a subsector exists only in the 2017 workbook
- **THEN** it is kept with vintage 2017

#### Scenario: Other levels ignored
- **WHEN** the workbook also lists 2-, 4-, 5- and 6-digit codes
- **THEN** none of them is in the subsector table

#### Scenario: Leading sequence column
- **WHEN** the first column of the sheet is a sequence number
- **THEN** the code and title are still read from their own columns

#### Scenario: Reproducible
- **WHEN** the script is run twice on the same workbooks
- **THEN** the output file is byte-for-byte identical

### Requirement: A facility's subsector
The system SHALL give each facility record its subsector: the first three digits of its NAICS code (`naics_subsector`) and that subsector's title from the local table (`naics_subsector_title`). A record with no NAICS code, a code shorter than three digits, or a subsector the table lacks SHALL have a null title, and a null code when the NAICS code is missing or shorter than three digits. The title SHALL come from the table, never be generated.

#### Scenario: Six-digit code
- **WHEN** the record's NAICS code is 325211
- **THEN** `naics_subsector` is "325" and `naics_subsector_title` is the table's title for 325

#### Scenario: Short or missing code
- **WHEN** the record's NAICS code is missing or "31"
- **THEN** `naics_subsector` and `naics_subsector_title` are null

#### Scenario: Unlisted subsector
- **WHEN** the code is "999999" and the table has no 999
- **THEN** `naics_subsector` is "999" and the title is null

### Requirement: Configuration, not code
The system SHALL read the subsector table's path and column names from the `[industry]` section of `config/settings.toml`, validated on load with errors naming the key.

#### Scenario: Another path
- **WHEN** the configured path is changed
- **THEN** the new file is read with no code change

#### Scenario: Missing column
- **WHEN** the table lacks a configured column
- **THEN** reading it raises a setup error naming the file and the column
