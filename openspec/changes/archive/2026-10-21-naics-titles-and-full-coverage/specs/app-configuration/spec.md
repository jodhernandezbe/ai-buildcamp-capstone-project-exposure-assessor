## MODIFIED Requirements

### Requirement: Industry settings
The system SHALL read from an `[industry]` table the Envirofacts path that lists the primary NAICS row of a submission (containing `{doc_ctrl_num}`) and the one that looks up a NAICS title (containing `{naics_code}`), the response field names (code, primary indicator, sequence, origin, title), the primary-indicator value, the origin labels for reported and assigned codes, the placeholder codes, and the local NAICS title table (`titles_path`, resolved against the project root, with the names of its code and title columns), validated on load, and SHALL NOT embed them in Python code. The base URL and request policy SHALL be the shared Envirofacts ones.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the industry settings
- **THEN** it returns the paths, field names, labels, placeholder codes and the titles table path and columns from the file

#### Scenario: Invalid entry
- **WHEN** a path lacks its placeholder, a field name, label or column name is empty, the titles path is empty, or a placeholder is not a digit string
- **THEN** the loader raises a `ValueError` naming the offending key

### Requirement: Web UI settings
The system SHALL read from a `[ui]` table, validated on load, and SHALL NOT embed these values
in Python or frontend code:
- the server host (loopback only) and port, and the built-frontend directory;
- the credential-store service name, the account name of each key (OpenAI, Census, CompTox) and the maximum accepted key length;
- the names of the scope classifier and scope addendum prompts, the fallback redirect prompt,
  and how many earlier messages the classifier sees;
- the names of the completion reviewer and nudge prompts, and the most nudges per user turn (a
  non-negative integer; zero turns the completion check off);
- the step label per tool name;
- the light and dark basemap style URLs, the initial map view (the bounds of the contiguous
  United States), the downwind sector half-angle (degrees), the marker size scale for emission
  rate, and the coordinate tolerance for matching receptors to facilities;
- the HQ threshold of concern and the lower bound of the "near" band, and the cancer-risk
  thresholds, each with a comment naming its basis;
- the suggestion chip texts, the significant digits for metrics, and the narrow-viewport
  breakpoint;
- the workspace layout limits: the collapsed rail width (px), the expanded rail's default,
  minimum and maximum width (px), the chat dock's default share of the viewport, its minimum
  width (px) and maximum share of the viewport, and the overview panel's default, minimum and
  maximum share of the analysis area;
- the maximum number of conversation threads held in memory;
- per-model token prices (USD per million input, cached input and output tokens) with the date
  and source they were taken from.
The frontend SHALL receive the display and layout settings it needs from an API endpoint, never
by duplicating them.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the UI settings
- **THEN** it returns the values from the file

#### Scenario: Invalid entry
- **WHEN** the port is out of range, the host is not a loopback address, a threshold or price is negative or a boolean, the "near" lower bound exceeds the threshold of concern, a prompt name is empty, or the nudge limit is negative or a boolean
- **THEN** the loader raises a `ValueError` naming the offending key

#### Scenario: Invalid layout limits
- **WHEN** a layout minimum exceeds its maximum, a default lies outside its limits, a share is not strictly between 0 and 1, a width is not a positive integer, or the thread maximum is not a positive integer
- **THEN** the loader raises a `ValueError` naming the offending key

#### Scenario: Completion check off
- **WHEN** `max_nudges` is 0
- **THEN** the program builds the agent without the completion check

#### Scenario: Frontend reads display settings
- **WHEN** the frontend starts
- **THEN** it fetches thresholds, map styles, the initial view, layout limits, chips and digits from the API instead of hard-coding them

## ADDED Requirements

### Requirement: FRS EIS settings
The system SHALL read from an `[frs_eis]` table the bulk FRS-to-EIS lookup and the same-site search: the service root URL, the EIS registrations path template (containing `{frs_ids}`), the site rows path template (containing `{frs_ids}`), the same-name path template (containing `{name}` and `{state}`), the answer field names (FRS ID, EIS ID, site name, state, latitude, longitude), `batch_size` (a positive integer) and `max_twin_distance_km` (a positive number), validated on load.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the FRS EIS settings
- **THEN** it returns the URL, path templates, field names, batch size and distance from the file

#### Scenario: Invalid entry
- **WHEN** a path lacks its placeholder or does not start with `/`, a field name is empty, `batch_size` is not a positive integer or the distance is not a positive number
- **THEN** the loader raises a `ValueError` naming the key
