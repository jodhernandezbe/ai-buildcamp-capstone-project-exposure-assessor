## ADDED Requirements

### Requirement: Read-across settings
The system SHALL read from a `[read_across]` table, validated on load, and SHALL NOT embed
these values in Python code:
- the PubChem PUG REST URL template, containing `{cas}`, and its request policy (timeout, delay, retries, backoff);
- the embedding model name and maximum token length;
- the fingerprint radius and bit count, and the embedding width;
- alpha, the applicability-domain threshold (calibrated against the catalog's leave-one-out
  score distribution, with that calibration recorded beside the value) and the catalog's column
  names;
- the catalog's shard directory, its shard file-name template (containing `{prefix}`) and the
  number of leading CAS digits that name a shard;
- the Envirofacts `tri_chem_info` path, containing `{start}` and `{end}`, and its page size;
- the CAS, name and inactive-date field names, the inactive-date value meaning "still listed", and whether delisted chemicals are kept (default: no).

The base URL and request policy for `tri_chem_info` SHALL be the shared Envirofacts ones.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the read-across settings
- **THEN** it returns the values from the file, with alpha 0.55 and threshold 0.60 by default

#### Scenario: Invalid entry
- **WHEN** alpha or the threshold is outside [0, 1] or boolean, the URL lacks `{cas}`, the `tri_chem_info` path lacks `{start}` or `{end}`, the shard template lacks `{prefix}`, the prefix length or the timeout, page size or a width or radius is not positive, or a column name is empty
- **THEN** the loader raises a `ValueError` naming the offending key

## MODIFIED Requirements

### Requirement: Agent chat model settings
The system SHALL read from an `[agent]` table the chat model that drives the agent: the
provider, the model name, the name of the environment variable holding the provider API key
(never the key itself), the request timeout, the step limit of one agent run and the sampling
temperature, validated on load, and SHALL NOT embed them in Python code. The shipped
temperature SHALL be 0, so a screening assessment is as reproducible as the provider allows.
The program and the agent evaluation SHALL both build the agent's chat model from this table
through one factory, so they always run the same model with the same temperature.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the agent settings
- **THEN** it returns the values from the file

#### Scenario: Changing the model
- **WHEN** the model name is edited
- **THEN** the program and the evaluations both use it with no code change

#### Scenario: Temperature reaches the model
- **WHEN** the agent's chat model is built from settings with temperature 0
- **THEN** the model samples at temperature 0

#### Scenario: Missing key
- **WHEN** the API-key variable is unset or blank and the chat model is built
- **THEN** building raises an error naming the variable

#### Scenario: Invalid entry
- **WHEN** a key is missing, the model name is empty, the provider is not supported, the timeout is not a positive number or is a boolean, the step limit is not a positive integer, or the temperature is missing, a boolean, or outside 0 to 2
- **THEN** the loader raises a `ValueError` naming the offending key
