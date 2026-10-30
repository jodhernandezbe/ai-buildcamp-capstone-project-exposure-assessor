## ADDED Requirements

### Requirement: Sessions table fits its pane
The sessions table SHALL never be wider than the analysis area. Started, question, estimated
cost and status SHALL always be visible; model and turns SHALL appear on a medium pane; model
calls, tool calls, tokens and duration SHALL appear only on a wide pane. A question longer than
its column SHALL be truncated with the whole question available as its tooltip. Every column
header SHALL be distinct.

#### Scenario: Narrow analysis area
- **WHEN** the analysis area is narrow (a 1280 px window with the chat open)
- **THEN** started, question, estimated cost and status are visible and nothing scrolls horizontally

#### Scenario: Medium analysis area
- **WHEN** the analysis area is medium (a 1920 px window with the chat open)
- **THEN** model and turns are visible too and nothing scrolls horizontally

#### Scenario: Wide analysis area
- **WHEN** the analysis area is wide enough for every column
- **THEN** every column is visible
