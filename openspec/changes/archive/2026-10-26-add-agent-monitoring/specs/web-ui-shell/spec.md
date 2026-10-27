## REMOVED Requirements

### Requirement: Navigation rail
**Reason**: "Monitoring" is no longer a disabled "Coming soon" placeholder: it opens the
Monitoring view, so the rail now switches between two views.
**Migration**: Replaced by "Navigation rail with workspace and monitoring views", which keeps every
other rule of this requirement and its scenarios.

## ADDED Requirements

### Requirement: Navigation rail with workspace and monitoring views
The leftmost region SHALL be a navigation rail with two states: collapsed (an icon rail of about
60 px) and expanded (resizable within its configured limits, 200–320 px by default). A toggle
next to the brand mark at the top SHALL switch between them. In order, the rail SHALL show: at
the top, the brand mark and the toggle. Below them, the entries "Workspace", "Clear workspace",
"Generate report" and "Monitoring". At the bottom, a Settings entry. The rail SHALL NOT list
runs and SHALL NOT offer a "New analysis" action. The entry for the view on screen
("Workspace" or "Monitoring") SHALL be marked as the current page, in words for assistive
technology and not by colour alone. Activating "Workspace" SHALL show the workspace, leave
fullscreen and close the Settings drawer and any open dialog. Activating "Monitoring" SHALL
show the Monitoring view and close the Settings drawer and any open dialog. The workspace
panels and the chat stay mounted and keep their state. In the collapsed state every entry SHALL
show only its icon with an accessible name and a tooltip; a disabled entry's tooltip SHALL say
why it is disabled.

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

#### Scenario: Open Monitoring
- **WHEN** the user activates "Monitoring"
- **THEN** the Monitoring view is shown, "Monitoring" is announced as the current page, and returning to "Workspace" shows the panels and chat as they were left
