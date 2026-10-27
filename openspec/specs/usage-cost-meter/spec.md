# usage-cost-meter Specification

## Purpose

Shows the user how many tokens each turn and the whole session consumed and roughly how much
money that cost, so the cost of an assessment is visible as it happens.

## Requirements

### Requirement: Token accounting per model call
The system SHALL record, for every chat model call of a turn (scope classifier and agent
calls), the model name and the provider-reported input tokens, cached input tokens and output
tokens. A call whose provider reports no usage SHALL be counted as a call with unknown usage
and flagged, never as zero tokens.

#### Scenario: Classifier counted
- **WHEN** a turn makes one classifier call and two agent calls
- **THEN** the turn's usage lists three calls, the classifier among them

#### Scenario: Missing usage
- **WHEN** a model call returns no usage metadata
- **THEN** the turn's usage is flagged incomplete and that call's tokens are unknown

### Requirement: Turn and session totals
After every turn (including a failed or redirected turn) the system SHALL emit the turn's
totals and the thread's running session totals of calls, input, cached input and output tokens
and estimated cost. Resetting the thread SHALL reset the session totals.

#### Scenario: Running total
- **WHEN** two turns use `a` and `b` input tokens
- **THEN** the session input total after the second turn is `a + b`

#### Scenario: Failed turn still billed
- **WHEN** a turn fails after two model calls
- **THEN** the usage event still reports those two calls

### Requirement: Cost from configured prices
The estimated cost in USD SHALL be computed only from per-model prices (USD per million input,
cached input and output tokens) in configuration, each model entry recording the date and the
source the prices were taken from. When the model has no configured price, or usage is
incomplete, the cost SHALL be reported as unpriced or as a lower bound respectively, never as a
guessed number. The cost SHALL be labelled an estimate.

#### Scenario: Priced model
- **WHEN** the model's prices are configured
- **THEN** the cost equals input x input price + cached x cached price + output x output price, all per million tokens

#### Scenario: Unpriced model
- **WHEN** the model has no price entry
- **THEN** tokens are reported and the cost is `null` with reason "unpriced"

#### Scenario: Invalid price entry
- **WHEN** a configured price is negative, non-numeric or a boolean
- **THEN** loading the configuration raises an error naming the key

### Requirement: Session cost for command-line runs
A command-line run SHALL be metered with the same accounting and prices as a web turn: every
model call is recorded, and the run's calls, input, cached input and output tokens and estimated
cost are printed after the answer. The cost SHALL be labelled an estimate and give its cost
status and the date of the prices. An unpriced model or incomplete usage SHALL be printed as
unpriced or as a lower bound, never as a guessed number.

#### Scenario: Summary after the answer
- **WHEN** a command-line run makes three priced model calls
- **THEN** the answer is followed by a summary of 3 calls, the token totals and the estimated cost in USD with its price date

#### Scenario: Unpriced model on the command line
- **WHEN** the configured model has no price entry
- **THEN** the summary gives the token totals and says the cost is unpriced
