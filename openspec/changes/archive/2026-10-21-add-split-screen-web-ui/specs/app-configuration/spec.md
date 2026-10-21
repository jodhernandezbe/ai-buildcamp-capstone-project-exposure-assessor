## MODIFIED Requirements

### Requirement: Agent chat model settings
The system SHALL read from an `[agent]` table the chat model that drives the agent: the
provider, the model name, the name of the environment variable holding the provider API key
(never the key itself), the request timeout, the step limit of one agent run and the sampling
temperature, validated on load, and SHALL NOT embed them in Python code. The shipped
temperature SHALL be 0, so a screening assessment is as reproducible as the provider allows.
The program, the web program and the agent evaluation SHALL all build the agent's chat model
from this table through one factory, so they always run the same model with the same
temperature. The factory SHALL accept the API key either injected as a secret value (from the
OS credential store) or read from the named environment variable when none is injected.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the agent settings
- **THEN** it returns the values from the file

#### Scenario: Changing the model
- **WHEN** the model name is edited
- **THEN** the program and the evaluations both use it with no code change

#### Scenario: Temperature reaches the model
- **WHEN** the agent's chat model is built from settings with temperature 0
- **THEN** the model samples at temperature 0

#### Scenario: Injected key
- **WHEN** the chat model is built with an injected key and the environment variable unset
- **THEN** the model is built with the injected key and the environment is not read

#### Scenario: Missing key
- **WHEN** no key is injected and the API-key variable is unset or blank and the chat model is built
- **THEN** building raises an error naming the variable

#### Scenario: Invalid entry
- **WHEN** a key is missing, the model name is empty, the provider is not supported, the timeout is not a positive number or is a boolean, the step limit is not a positive integer, or the temperature is missing, a boolean, or outside 0 to 2
- **THEN** the loader raises a `ValueError` naming the offending key

### Requirement: FRS point settings
The system SHALL read from an `[frs_point]` table the bulk FRS coordinates lookup: its service root URL (`base_url`, a separate service from Envirofacts `efservice`), the path template (containing `{frs_ids}`, a comma-separated list of FRS IDs), the answer field names of the FRS ID, latitude and longitude, and `batch_size`, the most FRS IDs asked in one request (a positive integer), validated on load.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the FRS point settings
- **THEN** it returns the base URL, path, field names and batch size from the file

#### Scenario: Invalid entry
- **WHEN** the path lacks `{frs_ids}`, a key is missing, or `batch_size` is not a positive integer
- **THEN** the loader raises a `ValueError` naming the key

### Requirement: Recent TRI years setting
The `[tri]` table SHALL define `recent_years` (a positive integer), `publication_lag_years` (a non-negative integer: TRI for year N is released by June of N + 1), `max_listed` (a positive integer, the most facilities the inventory tool lists to the model) and a `{after_year}` placeholder in the release path; the window ends with the current year minus `publication_lag_years`. The loader SHALL reject a missing, non-integer, boolean or out-of-range value and a path without the placeholder.

#### Scenario: Window years
- **WHEN** `recent_years` is 2, `publication_lag_years` is 1 and the current year is 2026
- **THEN** the settings give 2023 as the year after which reports count and 2024 as the first year

#### Scenario: Invalid window
- **WHEN** `recent_years` is 0, true or 2.5, `publication_lag_years` is -1, or `max_listed` is 0
- **THEN** the loader raises a `ValueError` naming the key

## ADDED Requirements

### Requirement: Web UI settings
The system SHALL read from a `[ui]` table, validated on load, and SHALL NOT embed these values
in Python or frontend code:
- the server host (loopback only) and port, and the built-frontend directory;
- the credential-store service name, the account name of each key (OpenAI, Census, CompTox) and the maximum accepted key length;
- the names of the scope classifier and scope addendum prompts, the fallback redirect prompt,
  and how many earlier messages the classifier sees;
- the step label per tool name;
- the light and dark basemap style URLs, the downwind sector half-angle (degrees), the marker
  size scale for emission rate, and the coordinate tolerance for matching receptors to
  facilities;
- the HQ threshold of concern and the lower bound of the "near" band, and the cancer-risk
  thresholds, each with a comment naming its basis;
- the suggestion chip texts, the significant digits for metrics, and the narrow-viewport
  breakpoint;
- per-model token prices (USD per million input, cached input and output tokens) with the date
  and source they were taken from.
The frontend SHALL receive the display settings it needs from an API endpoint, never by
duplicating them.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the UI settings
- **THEN** it returns the values from the file

#### Scenario: Invalid entry
- **WHEN** the port is out of range, the host is not a loopback address, a threshold or price is negative or a boolean, the "near" lower bound exceeds the threshold of concern, or a prompt name is empty
- **THEN** the loader raises a `ValueError` naming the offending key

#### Scenario: Frontend reads display settings
- **WHEN** the frontend starts
- **THEN** it fetches thresholds, map styles, chips and digits from the API instead of hard-coding them
