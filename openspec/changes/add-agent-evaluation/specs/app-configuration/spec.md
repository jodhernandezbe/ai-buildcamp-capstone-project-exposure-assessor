## ADDED Requirements

### Requirement: Agent chat model settings
The system SHALL read from an `[agent]` table the chat model that drives the agent: the
provider, the model name, the name of the environment variable holding the provider API key
(never the key itself), the request timeout and the step limit of one agent run, validated on
load, and SHALL NOT embed them in Python code. The program and the agent evaluation SHALL both
build the agent's chat model from this table through one factory, so they always run the same
model.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the agent settings
- **THEN** it returns the values from the file

#### Scenario: Changing the model
- **WHEN** the model name is edited
- **THEN** the program and the evaluations both use it with no code change

#### Scenario: Missing key
- **WHEN** the API-key variable is unset or blank and the chat model is built
- **THEN** building raises an error naming the variable

#### Scenario: Invalid entry
- **WHEN** a key is missing, the model name is empty, the provider is not supported, the timeout is not a positive number or is a boolean, or the step limit is not a positive integer
- **THEN** the loader raises a `ValueError` naming the offending key

### Requirement: Evaluation settings
The system SHALL read from an `[evaluation]` table: the judge model provider and name, the name
of the environment variable holding the judge provider's API key (never the key itself), the
names of the tools that run for real during replay (they need no network), the directory of
recorded tool outputs and the directory reports are written to, validated on load, and SHALL NOT
embed them in Python code. The agent's own model SHALL NOT be configured here.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the evaluation settings
- **THEN** it returns the values from the file, with relative directories resolved against the project root

#### Scenario: Changing the judge
- **WHEN** the judge model name is edited
- **THEN** subsequent evaluation runs use it with no code change

#### Scenario: Key variable name only
- **WHEN** the settings are read
- **THEN** they expose the environment variable name, not a key value

#### Scenario: Invalid entry
- **WHEN** a key is missing, the judge model name is empty, or the judge provider is not supported
- **THEN** the loader raises a `ValueError` naming the offending key
