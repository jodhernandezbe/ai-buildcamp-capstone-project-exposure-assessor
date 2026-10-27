## ADDED Requirements

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
