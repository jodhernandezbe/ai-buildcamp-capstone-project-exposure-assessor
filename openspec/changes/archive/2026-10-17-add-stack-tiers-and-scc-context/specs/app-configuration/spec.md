## ADDED Requirements

### Requirement: Stack parameter settings
The configuration SHALL hold, for the stack-parameter tools: the PSTK file path, its SCC column, an optional FIPS column with the values that mark national rows, the column and source unit of each of the four stack quantities, the target unit of each quantity, the plausible range (minimum and maximum, in target units) for each quantity, and the AirToxScreen global fallback values (3.0 m, 0.2 m, 4.0 m/s, 295.4 K). The loader SHALL return these as an immutable typed object.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the stack settings
- **THEN** it returns the PSTK path, column mapping, source and target units, plausible ranges and fallback values

#### Scenario: Invalid stack settings
- **WHEN** a fallback value is not a positive finite number, a range has minimum not below maximum, a fallback lies outside its range, or a quantity is missing from any table
- **THEN** the loader raises an error naming the offending entry

#### Scenario: Unconvertible source unit
- **WHEN** a configured source unit cannot be converted to its target unit
- **THEN** an error naming the quantity is raised before any lookup result is returned

### Requirement: SCC index settings
The configuration SHALL hold, for the SCC retrieval tool: the source table path, its column names, the persisted index directory, the collection name, the data categories and statuses to index, the number of results to return and the indexing batch size. It SHALL separately hold the embedding settings: provider name, model name, API-key environment variable name and request timeout. The loaders SHALL return these as immutable typed objects.

#### Scenario: Settings loaded
- **WHEN** the loaders are asked for the SCC index and embedding settings
- **THEN** they return every listed value from the file

#### Scenario: Invalid SCC index settings
- **WHEN** the result count, batch size or timeout is not a positive number, the category or status list is empty, a column name is missing, the provider is not a supported one, or the model name or collection name is blank
- **THEN** the loader raises an error naming the offending entry
