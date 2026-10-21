# web-ui-shell Specification

## Purpose

The split-screen browser interface: an executive dashboard and facility map on the left and the
copilot chat on the right, built to Apple Human Interface Guidelines materials and motion.

## Requirements

### Requirement: Locked split-screen shell
The interface SHALL fill exactly the viewport (`100dvh` x `100dvw`) without page scrolling,
with a left pane of 62–65% and a right pane of 35–38% of the width; each pane SHALL scroll or
pan independently. Below a configured narrow-viewport breakpoint the panes SHALL stack with a
segmented control to switch between Overview and Copilot, still without page-level scroll.

#### Scenario: Desktop
- **WHEN** the window is 1440 x 900
- **THEN** the left pane is between 62% and 65% wide, the right between 35% and 38%, and the document does not scroll

#### Scenario: Long chat
- **WHEN** the chat holds more messages than fit
- **THEN** only the chat list scrolls; the ribbon and map stay fixed

### Requirement: Apple HIG visual language
Surfaces SHALL use translucent materials (`backdrop-filter: blur(20px)` with a solid fallback
where unsupported), 1px hairline borders (`rgba(0,0,0,0.08)` light, `rgba(255,255,255,0.1)`
dark), the system font stack (`-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro
Text"`, Inter fallback, sans-serif), and tabular numerals for every metric. Transitions SHALL
use `cubic-bezier(0.22, 1, 0.36, 1)`. The interface SHALL follow the OS light/dark preference,
and SHALL disable non-essential motion when the user prefers reduced motion. Text and status
colours SHALL meet WCAG AA contrast, and status SHALL never be conveyed by colour alone.

#### Scenario: Dark mode
- **WHEN** the OS is in dark mode
- **THEN** the interface, the basemap and hairlines switch to their dark variants

#### Scenario: Reduced motion
- **WHEN** the user prefers reduced motion
- **THEN** camera moves jump instead of fly and spring transitions are replaced by fades

### Requirement: Scientific notation and units
Every metric SHALL be shown with its unit; very small or large values (such as cancer risk)
SHALL use scientific notation rendered as `1.2 × 10⁻⁵`; the number of significant digits
SHALL come from configuration; absent values SHALL show "not reported" (or the reason given in
the state) rather than zero or a dash that could be read as zero. Values the UI did not receive
SHALL NOT be shown.

#### Scenario: Cancer risk
- **WHEN** the state reports a cancer risk of 0.000012
- **THEN** it renders as `1.2 × 10⁻⁵`

#### Scenario: Absent value
- **WHEN** a facility has no exit temperature
- **THEN** the inspector shows "not reported" for it

### Requirement: Executive summary ribbon
The top of the left pane SHALL show four cards updated from each `workspace_update` event:
1. HQ and cancer risk: highest worst-case and representative values with a status pill
   (green below, amber near, red above the threshold of concern, each also labelled in words);
2. Chemical and read-across provenance: CAS, molecular weight, RfC/IUR with sources, and a badge
   "Direct TRI match", "Read-across surrogate" (surrogate CAS/name, hybrid score, cosine,
   Tanimoto, in/out of applicability domain), "Unresolved" or "Not evaluated";
3. Exposed population: total within the radius `r` km and a horizontal stacked bar of the age
   bands 0-4, 5-17, 18-64, 65+, with the data source;
4. Meteorology: wind speed (m/s), a direction arrow pointing downwind with the from-direction in
   degrees, ambient temperature (K), Pasquill-Gifford class and source.
Cards whose data comes from a screening default SHALL show a "screening default" marker.

#### Scenario: Surrogate badge
- **WHEN** the state reports a read-across surrogate within the domain
- **THEN** card 2 shows the surrogate badge with its hybrid score and "within applicability domain"

#### Scenario: Default weather
- **WHEN** meteorology's source is the screening default
- **THEN** card 4 shows the screening-default marker

### Requirement: Interactive facility map
The left pane SHALL show a vector basemap (light and dark styles from configuration) with one
marker per placed facility, coloured by its risk status (or neutral when not computed) and sized
by emission rate on a configured scale, with a legend. When the framing version changes the
camera SHALL animate to fit the bounding box. For a facility with receptors the map SHALL draw
the receptor radius circle, and with meteorology SHALL draw a sector toward
`(wind_direction + 180) % 360` with a configured half-angle and the radius as length, labelled
"schematic downwind sector — not a modelled plume footprint".

#### Scenario: Fit to facilities
- **WHEN** a dashboard event raises the framing version
- **THEN** the camera flies to fit all placed facilities

#### Scenario: Downwind sector
- **WHEN** the wind blows from 270°
- **THEN** the sector points toward 90°

### Requirement: Facility inspector popover
Hovering or keyboard-focusing a marker SHALL open a translucent inspector anchored to it, and
it SHALL close on leave, blur or Escape. It SHALL show: facility name, FRS ID, TRI document
control number, NAICS code and title; reported release with its unit, emission rate (g/s),
operating hours (h/yr) and CAS; each stack's height (m), diameter (m), exit velocity (m/s), exit
temperature (K) with its provenance tier pill; and receptor metrics: worst-case and
representative maximum concentration (µg/m³), HQ, cancer risk and population within the
radius. Markers SHALL be reachable by keyboard and announce the facility name to screen readers.

#### Scenario: Keyboard focus
- **WHEN** a marker receives keyboard focus
- **THEN** the inspector opens for that facility and Escape closes it

#### Scenario: Several stacks
- **WHEN** the facility has three NEI candidates
- **THEN** the inspector lists all three with Tier 1 pills and the HQ range across them

### Requirement: Copilot chat
The right pane SHALL show a header with the title, a live status indicator (idle, thinking,
running a tool, error), the usage meter and a gear button at the top right. An empty thread
SHALL show an onboarding state with three to four suggestion chips (text from configuration)
that submit their text when clicked. Assistant messages SHALL render Markdown safely (no raw
HTML) and stream as `token` events arrive. Tool steps SHALL appear as compact pills,
grouped per turn in a collapsible row, each showing its label and a running / done / error
state. Off-topic redirects SHALL render as normal assistant messages. A "New assessment"
action SHALL reset the thread.

#### Scenario: Suggestion chip
- **WHEN** the user clicks a suggestion chip
- **THEN** its text is sent as the user's message and the onboarding state disappears

#### Scenario: Tool pills
- **WHEN** a turn runs four tools
- **THEN** one collapsed row shows four pills that expand on click

#### Scenario: No raw HTML
- **WHEN** an assistant message contains `<script>`
- **THEN** it is shown as text and not executed

### Requirement: Settings sheet for the API keys
Clicking the gear SHALL open a modal sheet (focus-trapped, closable with Escape) with one section
per key (OpenAI, Census, CompTox), each stating what it is used for (the OpenAI key runs the
assistant, the Census key counts the people around a facility, the CompTox key looks up chemical
properties and toxicity) and having a password-type input, a status badge "Key stored securely in
OS Keychain" or "No key configured" (never any part of the key), a "Save" button and a
"Clear key" action. Saving or clearing one key SHALL NOT affect the others. Inputs SHALL be
cleared after saving, and no key SHALL be written to browser storage, the URL or logs. Only the
OpenAI key is required: when it is not configured the chat input SHALL point the user to
Settings, and when the Census or CompTox key is missing the sheet SHALL say which lookups will be
unavailable.

#### Scenario: Save key
- **WHEN** the user enters a key in a section and saves
- **THEN** that section's badge shows the stored state, showing no part of the key, and its input is empty, and the other sections are unchanged

#### Scenario: Optional keys missing
- **WHEN** only the OpenAI key is stored
- **THEN** the Census and CompTox sections say which lookups are unavailable until their keys are saved

#### Scenario: No browser storage
- **WHEN** a key has been saved
- **THEN** `localStorage` and `sessionStorage` contain no key material

### Requirement: Usage meter
The chat header SHALL show the session's total tokens and estimated cost, and a popover SHALL
break them down by input, cached input and output tokens for the last turn and the session,
marking the cost as an estimate, "unpriced" or "lower bound" as reported.

#### Scenario: After a turn
- **WHEN** a `usage` event arrives
- **THEN** the meter updates to the new session totals

#### Scenario: Unpriced
- **WHEN** the usage event's cost is unpriced
- **THEN** the meter shows tokens and "unpriced" instead of a dollar amount
