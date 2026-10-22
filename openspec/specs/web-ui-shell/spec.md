# web-ui-shell Specification

## Purpose

The split-screen browser interface: an executive dashboard and facility map on the left and the
copilot chat on the right, built to Apple Human Interface Guidelines materials and motion.

## Requirements

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
2. Chemical and read-across provenance: name (when the state has one; otherwise the CAS number stands alone, never a name from elsewhere), CAS, molecular weight, RfC/IUR with sources, and a badge
   "Direct TRI match", "Read-across surrogate" (surrogate CAS/name, hybrid score, cosine,
   Tanimoto, in/out of applicability domain), "Unresolved" or "Not evaluated";
3. Exposed population: total within the radius `r` km and a horizontal stacked bar of the age
   bands 0-4, 5-17, 18-64, 65+, with the data source;
4. Meteorology: the facility it is for (or, for a point that is not one of the facilities, its
   coordinates and that fact), wind speed (m/s), a direction arrow pointing downwind with the from-direction in
   degrees, ambient temperature (K), Pasquill-Gifford class and source.
Cards whose data comes from a screening default SHALL show a "screening default" marker.

#### Scenario: Surrogate badge
- **WHEN** the state reports a read-across surrogate within the domain
- **THEN** card 2 shows the surrogate badge with its hybrid score and "within applicability domain"

#### Scenario: Default weather
- **WHEN** meteorology's source is the screening default
- **THEN** card 4 shows the screening-default marker

#### Scenario: Chemical name
- **WHEN** the state's chemical has a name
- **THEN** card 2 shows it before the CAS number; when it has none, card 2 shows the CAS number only

### Requirement: Interactive facility map
The analysis area SHALL show a vector basemap (light and dark styles from configuration) as soon
as the page loads, framed on the configured initial view (the contiguous United States), even
when no facility has been placed. It SHALL draw one marker per placed facility, coloured by its
risk status (or neutral when not computed) and sized by emission rate on a configured scale,
with a legend. When the framing version changes, the camera SHALL animate to fit the bounding
box, with padding that keeps the framed facilities clear of the legend. The map SHALL redraw at
its new size whenever its container changes size (splitter drag, rail or chat collapse, panel
fullscreen, window resize), leaving no blank or stretched area. A "Reset to USA view" control
on the map SHALL return the camera to the configured initial view. It SHALL animate, or jump
when the user prefers reduced motion. For a facility with receptors the map SHALL draw the
receptor radius circle. With meteorology it SHALL draw a sector toward
`(wind_direction + 180) % 360` with a configured half-angle and the radius as length, labelled
"schematic downwind sector — not a modelled plume footprint".

#### Scenario: Before any query
- **WHEN** the page has loaded and no assessment has run
- **THEN** the basemap is visible, framed on the contiguous United States, with no markers

#### Scenario: Fit to facilities
- **WHEN** a dashboard event raises the framing version
- **THEN** the camera flies to fit all placed facilities

#### Scenario: Container resized
- **WHEN** the user collapses the chat dock
- **THEN** the map fills the wider area without blank tiles or distortion

#### Scenario: Reset view
- **WHEN** facilities are framed and the user activates "Reset to USA view"
- **THEN** the camera returns to the contiguous United States and the markers stay placed

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
The chat dock SHALL show a header with the title, a live status indicator (idle, thinking,
running a tool, error), the usage meter and a collapse control. An empty thread SHALL show an
onboarding state with three to four suggestion chips (text from configuration) that submit their
text when clicked. Assistant messages SHALL render Markdown safely (no raw HTML), including
GitHub Flavored Markdown tables, and stream as `token` events arrive. A table SHALL render as a
real table with a header row. It SHALL sit in its own horizontal scroll area, so a table wider
than the message scrolls sideways without widening the message, the chat or the page. The header
SHALL be shaded, all columns SHALL use tabular numerals, and cell text SHALL NOT wrap. Tool steps
SHALL appear as compact pills, grouped per turn in a collapsible row, each showing its label and
a running / done / error state. Off-topic redirects SHALL render as normal assistant messages.
Starting a new analysis is done from the navigation rail.

#### Scenario: Suggestion chip
- **WHEN** the user clicks a suggestion chip
- **THEN** its text is sent as the user's message and the onboarding state disappears

#### Scenario: Tool pills
- **WHEN** a turn runs four tools
- **THEN** one collapsed row shows four pills that expand on click

#### Scenario: No raw HTML
- **WHEN** an assistant message contains `<script>`
- **THEN** it is shown as text and not executed

#### Scenario: Pipe table
- **WHEN** an assistant message contains a GFM pipe table with a header row
- **THEN** it renders as a table with header cells and body rows, not as literal pipes

#### Scenario: Wide table
- **WHEN** a rendered table is wider than the chat dock
- **THEN** only that table scrolls horizontally and the chat dock width is unchanged

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

### Requirement: The assistant does not describe what it cannot see
In the web program the assistant SHALL be told that it cannot see the overview or the map, what
the map shows (every facility the inventory found, not only those listed to it) and how details
open (pointing at or moving to a marker), and SHALL say no more about the map than that.

#### Scenario: Asked to show the map
- **WHEN** the user asks the assistant to show or explain the map
- **THEN** the assistant describes only what the map places and how to open a facility's details, and speaks of its own results otherwise

### Requirement: Resizable workspace shell
The interface SHALL fill exactly the viewport (`100dvh` x `100dvw`) without page scrolling and
SHALL be divided, left to right, into a navigation rail, an analysis area and a chat dock. Each
region SHALL scroll or pan independently. Adjacent regions SHALL be separated by a splitter that
can be dragged with a pointer and moved with the arrow keys when focused. Each splitter SHALL
show a 2–4 px accent line on hover, focus and drag, show a resize cursor, and announce itself to
assistive technology as a separator with its current value. Every region SHALL keep to the
minimum and maximum sizes given by configuration: the chat dock at least its configured minimum
width in px and at most its configured maximum share of the viewport width. Panel sizes SHALL be
remembered in browser storage for the same viewer (sizes and collapsed states only), clamped to the current limits
when restored. Below the configured narrow-viewport breakpoint the rail SHALL collapse to icons
and the analysis area and chat SHALL stack behind a segmented control (Overview, Copilot), still
without page-level scroll. Both stay mounted, so nothing is lost when switching.

#### Scenario: Desktop
- **WHEN** the window is 1440 x 900 on first load
- **THEN** the rail, analysis area and chat dock are all visible within their configured limits and the document does not scroll

#### Scenario: Drag the chat splitter
- **WHEN** the user drags the splitter between the analysis area and the chat dock past the chat's configured maximum
- **THEN** the chat dock stops at its maximum share of the viewport and the map redraws at the new size

#### Scenario: Keyboard resize
- **WHEN** a splitter has keyboard focus and the user presses an arrow key
- **THEN** the adjacent regions resize by one step within their limits

#### Scenario: Long chat
- **WHEN** the chat holds more messages than fit
- **THEN** only the chat list scrolls; the overview and map stay fixed

#### Scenario: Restored sizes out of range
- **WHEN** a remembered chat width exceeds the current window's maximum
- **THEN** the dock opens at the maximum, not at the remembered width

### Requirement: Settings drawer for the API keys
Choosing Settings in the navigation rail SHALL open a bottom drawer over the workspace. The drawer
SHALL keep the workspace and the chat mounted, can be resized and maximized, closes with
Escape or its close control, and keeps focus inside it while open, returning focus on close. The
drawer SHALL hold collapsible sections: an Assistant section for the OpenAI key and a Data
services section for the Census and CompTox keys. Each key SHALL have a label with an info
tooltip stating what it is used for (the OpenAI key runs the assistant, the Census key counts the
people around a facility, the CompTox key looks up chemical properties and toxicity), a
password-type input that can be cleared, a status reading "Key stored securely in OS Keychain"
or "No key configured" (never any part of the key), and "Clear key", "Reset" and "Save"
actions. Save SHALL be disabled while the input is blank or a request is running. The outcome of
a save or clear SHALL be shown in an inline success or error message in that key's section.
Saving or clearing one key SHALL NOT affect the others. Inputs SHALL be cleared after saving and
by Reset, and no key SHALL be written to browser storage, the URL or logs. Only the OpenAI key is
required: when it is not configured, the chat input SHALL point the user to Settings and the
Assistant section SHALL open expanded. When the Census or CompTox key is missing, its section
SHALL say which lookups will be unavailable.

#### Scenario: Open from the rail
- **WHEN** the user activates Settings in the navigation rail
- **THEN** the drawer opens over the workspace and the map and chat stay as they were

#### Scenario: Save key
- **WHEN** the user enters a key in a section and saves
- **THEN** that section shows a success message and the stored state, showing no part of the key, its input is empty, and the other sections are unchanged

#### Scenario: Save fails
- **WHEN** the server rejects a key
- **THEN** that section shows an error message and the stored state is unchanged

#### Scenario: Optional keys missing
- **WHEN** only the OpenAI key is stored
- **THEN** the Census and CompTox entries say which lookups are unavailable until their keys are saved

#### Scenario: No browser storage
- **WHEN** a key has been saved
- **THEN** `localStorage` and `sessionStorage` contain no key material

### Requirement: Navigation rail
The leftmost region SHALL be a navigation rail with two states: collapsed (an icon rail of about
60 px) and expanded (resizable within its configured limits, 200–320 px by default). A toggle
next to the brand mark at the top SHALL switch between them. In order, the rail SHALL show:
at the top, the brand mark, the toggle and a "New analysis" action. In the middle, a
"Workspace" entry and the list of this session's runs. At the bottom, a Settings entry. In the
collapsed state every entry SHALL show only its icon with an accessible name and a tooltip. The
current run SHALL be marked as current, in words for assistive technology and not by colour
alone.

#### Scenario: Collapse and expand
- **WHEN** the user activates the toggle on an expanded rail
- **THEN** the rail collapses to icons, the analysis area widens, and the map redraws at its new size

#### Scenario: Collapsed entries remain usable
- **WHEN** the rail is collapsed and the user focuses the Settings icon
- **THEN** it announces "Settings" and opens the settings drawer when activated

### Requirement: Session run history
"New analysis" SHALL start a new, empty conversation and workspace without discarding the
previous run. The rail SHALL list the runs of the current page session, newest first. Each run
is titled by its first user message, shortened, or "New analysis" while it has none. Selecting a
run SHALL restore its messages, workspace (overview and map) and session usage from the server
and make it the conversation that new messages continue. A run whose turn is still streaming
SHALL NOT be switched away from until the turn ends or is stopped. If the server no longer holds
a run (restarted or evicted), selecting it SHALL show that the run is no longer available and
remove it from the list, leaving the current conversation unchanged. Restored assistant messages
show their text; tool-step pills are shown only for turns streamed in this page session. The
list SHALL NOT be written to browser storage.

#### Scenario: Start a second run
- **WHEN** a run has messages and the user activates "New analysis"
- **THEN** an empty conversation and an empty map framed on the United States appear, and the earlier run is listed in the rail

#### Scenario: Return to an earlier run
- **WHEN** the user selects an earlier run in the rail
- **THEN** its messages, overview and map are restored and the next message continues that run

#### Scenario: Run no longer available
- **WHEN** the user selects a run the server has evicted
- **THEN** a message says the run is no longer available, the run leaves the list, and the current conversation is unchanged

### Requirement: Analysis panels with fullscreen
The analysis area SHALL hold an Overview panel (the executive summary) and a Map panel, each
with a header naming it. They SHALL be separated by a splitter that can be dragged, with the
same behavior and configured limits as the other splitters. Each panel header SHALL have a
fullscreen toggle with an accessible name ("Enter fullscreen" / "Exit fullscreen"). Entering
fullscreen SHALL make that panel fill the whole workspace (rail, other panel and chat hidden but
still mounted). Exiting, by the toggle or by Escape, SHALL restore the previous layout and sizes.
Escape SHALL close an open inspector or drawer before it exits fullscreen.

#### Scenario: Map fullscreen
- **WHEN** the user activates the Map panel's fullscreen toggle
- **THEN** the map fills the workspace, redraws at the new size, and keeps its markers and camera

#### Scenario: Escape exits
- **WHEN** a panel is fullscreen and no inspector or drawer is open and the user presses Escape
- **THEN** the previous layout and panel sizes are restored

#### Scenario: Chat state survives fullscreen
- **WHEN** a turn is streaming and the user toggles the Overview panel fullscreen and back
- **THEN** the chat has kept receiving the streamed answer

### Requirement: Collapsible chat dock
The chat dock header SHALL have a collapse control that hides the dock against the right edge,
giving its width to the analysis area. While collapsed, a visible control on the right edge
SHALL restore the dock with one click at its previous width. Collapsing SHALL NOT interrupt a
streaming turn or discard the draft in the composer.

#### Scenario: Collapse during a turn
- **WHEN** a turn is streaming and the user collapses the chat
- **THEN** the analysis area takes the full width and, on restore, the streamed answer is complete or still streaming with nothing lost

### Requirement: Results table in the Overview panel
Below the ribbon, the Overview panel SHALL show a table built only from the workspace state, one row per facility the state holds, with: name and FRS ID, state, emission rate (g/s), screening outcome (fully assessed, worst case only, screened out on the bound or with its own stacks, not assessed), stack tier, worst-case and representative HQ and cancer risk (ranges over the stacks, "not reported" when absent), residents within the radius, and the status pill. Rows SHALL be ordered by the status then the worst-case HQ, highest first, with a column-header sort the user can change; screened-out and unassessed facilities SHALL sit in a folded group below the assessed ones with their count, and a facility's screening value SHALL show in place of its HQ when it was screened out. Selecting a row SHALL open that facility on the map. The table SHALL use tabular numerals, scroll horizontally in a narrow panel, and SHALL never compute or convert a value.

#### Scenario: Every facility present
- **WHEN** the state holds 1,231 facilities of which 157 were assessed
- **THEN** the table lists all 157 assessed rows and a folded group "1,074 screened out or not assessed"

#### Scenario: Sorted by risk
- **WHEN** the table first renders
- **THEN** facilities above concern come first, each group by worst-case HQ descending

#### Scenario: Screened-out row
- **WHEN** a facility was screened out on the bound at HQ 0.05
- **THEN** its row shows "screened out (bound HQ 0.05)" and no representative values

#### Scenario: Row opens the facility
- **WHEN** the user activates a row
- **THEN** the map frames that facility and its card opens
