## MODIFIED Requirements

### Requirement: Web UI settings
The system SHALL read from a `[ui]` table, validated on load, and SHALL NOT embed these values
in Python or frontend code:
- the server host (loopback only) and port, and the built-frontend directory;
- the credential-store service name, the account name of each key (OpenAI, Census, CompTox) and the maximum accepted key length;
- the names of the scope classifier and scope addendum prompts, the fallback redirect prompt,
  and how many earlier messages the classifier sees;
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
- **WHEN** the port is out of range, the host is not a loopback address, a threshold or price is negative or a boolean, the "near" lower bound exceeds the threshold of concern, or a prompt name is empty
- **THEN** the loader raises a `ValueError` naming the offending key

#### Scenario: Invalid layout limits
- **WHEN** a layout minimum exceeds its maximum, a default lies outside its limits, a share is not strictly between 0 and 1, a width is not a positive integer, or the thread maximum is not a positive integer
- **THEN** the loader raises a `ValueError` naming the offending key

#### Scenario: Frontend reads display settings
- **WHEN** the frontend starts
- **THEN** it fetches thresholds, map styles, the initial view, layout limits, chips and digits from the API instead of hard-coding them
