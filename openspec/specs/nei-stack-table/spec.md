# nei-stack-table Specification

## Purpose

The compact local table of NEI stack values that tier 1 reads, and the script that builds it from the raw NEI SMOKE point flat file.

## Requirements


### Requirement: Compact sharded stack table
The system SHALL keep the NEI stack values as gzip-compressed CSV shards, one file per leading digit(s) of the EIS ID (the number of digits configured), each with the EIS ID and the four stack values, one row per distinct combination. Each shard SHALL be smaller than the repository's large-file limit. A lookup SHALL read only the shard of its ID prefix.

#### Scenario: Shard selection
- **WHEN** an EIS ID is looked up
- **THEN** only the shard named for its first configured digits is read

#### Scenario: Shard cached
- **WHEN** the same shard is read twice without the file changing
- **THEN** the second read does not parse the file again

#### Scenario: Unreadable shard
- **WHEN** the shard file is missing or corrupt
- **THEN** the lookup returns no values for that ID and a warning, without raising

### Requirement: Reproducible build from the raw file
The system SHALL provide a script that streams the raw NEI SMOKE point flat file (a zip) without unpacking it, ignores comment lines, keeps only the configured columns, drops rows whose facility ID is not a digit string or whose four values are not finite and positive, removes duplicates, and writes the shards. The output SHALL be byte-for-byte reproducible and sorted, and stale shards SHALL be removed. The raw file SHALL NOT be committed.

#### Scenario: Pollutant rows collapse
- **WHEN** a release point has many pollutant rows with the same stack values
- **THEN** the shard holds one row for that combination

#### Scenario: Invalid rows dropped
- **WHEN** a row has a blank, zero, negative or non-numeric stack value, or a non-digit facility ID
- **THEN** it is not written

#### Scenario: Reproducible
- **WHEN** the script runs twice on the same input
- **THEN** the shard files are identical

#### Scenario: Missing column
- **WHEN** the raw file lacks a configured column
- **THEN** the script reports it and writes nothing
