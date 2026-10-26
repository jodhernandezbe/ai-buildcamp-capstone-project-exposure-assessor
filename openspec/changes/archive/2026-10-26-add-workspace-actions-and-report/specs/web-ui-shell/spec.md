## MODIFIED Requirements

### Requirement: Navigation rail
The leftmost region SHALL be a navigation rail with two states: collapsed (an icon rail of about
60 px) and expanded (resizable within its configured limits, 200–320 px by default). A toggle
next to the brand mark at the top SHALL switch between them. In order, the rail SHALL show: at
the top, the brand mark and the toggle. Below them, the entries "Workspace", "Clear workspace",
"Generate report" and "Monitoring". At the bottom, a Settings entry. The rail SHALL NOT list
runs and SHALL NOT offer a "New analysis" action. "Workspace" SHALL be marked as the current
page, in words for assistive technology and not by colour alone; activating it SHALL leave
fullscreen and close the Settings drawer and any open dialog. "Monitoring" SHALL be shown
disabled with the note "Coming soon" and SHALL do nothing when activated. In the collapsed
state every entry SHALL show only its icon with an accessible name and a tooltip; a disabled
entry's tooltip SHALL say why it is disabled.

#### Scenario: Collapse and expand
- **WHEN** the user activates the toggle on an expanded rail
- **THEN** the rail collapses to icons, the analysis area widens, and the map redraws at its new size

#### Scenario: Collapsed entries remain usable
- **WHEN** the rail is collapsed and the user focuses the Settings icon
- **THEN** it announces "Settings" and opens the settings drawer when activated

#### Scenario: Entries in order
- **WHEN** the rail is expanded
- **THEN** it shows Workspace, Clear workspace, Generate report and Monitoring in that order, then Settings at the bottom, and no run list

#### Scenario: Return to the workspace
- **WHEN** the map is fullscreen and the Settings drawer is open, and the user activates "Workspace"
- **THEN** the drawer closes and the overview, map and chat are all visible again

#### Scenario: Monitoring not yet available
- **WHEN** the user activates "Monitoring"
- **THEN** nothing changes and the entry is announced as unavailable with "Coming soon"

### Requirement: Copilot chat
The chat dock SHALL show a header with the title, a live status indicator (idle, thinking,
running a tool, error), the usage meter, a clear control and a collapse control. An empty thread
SHALL show an onboarding state with three to four suggestion chips (text from configuration)
that submit their text when clicked. Assistant messages SHALL render Markdown safely (no raw
HTML), including GitHub Flavored Markdown tables, and stream as `token` events arrive. A table
SHALL render as a real table with a header row. It SHALL sit in its own horizontal scroll area,
so a table wider than the message scrolls sideways without widening the message, the chat or
the page. The header SHALL be shaded, all columns SHALL use tabular numerals, and cell text
SHALL NOT wrap. Tool steps SHALL appear as compact pills, grouped per turn in a collapsible row,
each showing its label and a running / done / error state. Off-topic redirects SHALL render as
normal assistant messages. The chat header's clear control SHALL perform the same "Clear
workspace" action as the navigation rail, including its confirmation.

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

#### Scenario: Chat clear asks first
- **WHEN** the user activates the chat header's clear control on a workspace with results
- **THEN** the same confirmation dialog as "Clear workspace" opens

## ADDED Requirements

### Requirement: Clear workspace
"Clear workspace" SHALL open an in-app confirmation dialog (not a browser dialog) that says the
conversation, overview, charts and map will be discarded and cannot be recovered, with "Clear"
and "Cancel" actions; Cancel and Escape SHALL close it without changes, and focus SHALL return
to the control that opened it. On "Clear" the interface SHALL ask the server to discard the
current thread and then show an empty chat (onboarding state), an empty overview, no charts,
and an empty map framed on the United States, with the usage meter reset and any pending
confirmation card removed; the next message SHALL start a new thread. If the server cannot
discard the thread, the interface SHALL say so and keep the current workspace unchanged. The
entry SHALL be disabled while a turn streams and when the workspace is already empty (no
messages and no results).

#### Scenario: Clear after an assessment
- **WHEN** the workspace shows messages, facilities and charts and the user confirms "Clear"
- **THEN** the chat shows the onboarding state, the overview and charts are empty, the map shows the United States with no facilities, and the usage meter reads zero

#### Scenario: Cancel
- **WHEN** the confirmation dialog is open and the user presses Escape
- **THEN** the dialog closes, the workspace is unchanged and focus returns to "Clear workspace"

#### Scenario: Disabled while streaming
- **WHEN** a turn is streaming
- **THEN** "Clear workspace" is disabled and its tooltip says a reply is in progress

#### Scenario: Server refuses
- **WHEN** the user confirms "Clear" and the server answers with an error
- **THEN** a message says the workspace could not be cleared and every message, result and map layer is still shown

### Requirement: Generate report
"Generate report" SHALL request the current thread's Word report from the server and save it
through the browser as a `.docx` file named by the server. While the request runs the entry
SHALL show a busy state and SHALL NOT start a second request. The entry SHALL be disabled while
a turn streams and while the workspace holds neither a chemical result nor a facility, with a
tooltip saying why. If the request fails, the interface SHALL show the server's generic message
and leave the workspace unchanged. The interface SHALL NOT build or alter the report's content.

#### Scenario: Download a report
- **WHEN** the workspace holds an assessed facility and the user activates "Generate report"
- **THEN** a `.docx` file is downloaded and the workspace is unchanged

#### Scenario: Nothing to report
- **WHEN** the workspace is empty
- **THEN** "Generate report" is disabled and its tooltip says there are no findings yet

#### Scenario: Report fails
- **WHEN** the server answers the report request with an error
- **THEN** a message with the generic error text is shown and no file is saved

## REMOVED Requirements

### Requirement: Session run history
**Reason**: The interface now holds a single workspace; the run list and "New analysis" were
confusing and did not survive a page reload.
**Migration**: Use "Clear workspace" to start over. Save findings with "Generate report" before
clearing.
