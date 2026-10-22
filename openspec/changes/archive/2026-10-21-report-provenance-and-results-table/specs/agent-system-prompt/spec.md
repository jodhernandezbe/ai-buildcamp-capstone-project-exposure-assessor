## MODIFIED Requirements

### Requirement: Evidence quality, alternatives and honesty
The prompt SHALL state that facility-specific evidence is preferred over process-typical and that over generic defaults, that a more generic source is used only when a better one is unavailable and is then disclosed, that several credible alternatives are each evaluated and reported as a range, that worst-case and typical results are both reported, that numbers, names and identifiers are never invented, estimated or converted by the agent (a chemical is called by the name a tool result gives, else by its CAS number alone), that a branch with no defensible answer is stopped with the reason, and that the user is asked when something essential and not obtainable by a tool is missing.

#### Scenario: Default in the data
- **WHEN** the prompt is read
- **THEN** it requires the final answer to say which inputs were defaults or generic and why

#### Scenario: Alternatives
- **WHEN** the prompt is read
- **THEN** it says to evaluate every credible alternative and report the range

#### Scenario: Chemical without a name
- **WHEN** the properties result carries no name for the chemical
- **THEN** the prompt requires the report to refer to it by its CAS number and never to supply a name

### Requirement: Output format and structure
The prompt SHALL ask for a short summary, per-facility results with units, ranges and the origin of each input named as the results name it (the source text of the weather, the residents, the stacks' tier and the toxicity benchmarks), plain-language comment on results beyond a health benchmark, and a Limitations section listing the method's limits, defaults or generic inputs and data gaps, and SHALL be structured with the `role`, `context`, `instructions` and `output_format` XML tags in that order. When the assessment cannot start because something only the user can give is missing, the prompt SHALL ask for a reply containing just that request and why it is needed, not the report format.

#### Scenario: Structure
- **WHEN** the prompt is loaded
- **THEN** it contains the four tags in that order

#### Scenario: Sources as the results give them
- **WHEN** the prompt is read
- **THEN** it asks that each input's source be named with the text the result gives, not paraphrased ("actual local weather" is not a source)

#### Scenario: Nothing to report yet
- **WHEN** the assessment cannot start because the user has not given the chemical's CAS number
- **THEN** the reply is the request alone, with no summary, results table or Limitations section
