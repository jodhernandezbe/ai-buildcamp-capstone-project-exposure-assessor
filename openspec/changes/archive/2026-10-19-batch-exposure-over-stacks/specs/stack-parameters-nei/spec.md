## MODIFIED Requirements

### Requirement: Tool description orders the tiers and the scenarios
The NEI tool's description, as seen by the LLM, SHALL state that it is the first choice for stack parameters, that it returns several candidate stacks which are ALL to be passed together to one exposure calculation (never a subset) whose returned range is what to report, that omitted taller stacks are announced in the warnings and belong in the report, and that the SCC-based tool is to be used only when it returns no candidates.

#### Scenario: Description content
- **WHEN** the tool's description is read
- **THEN** it names the tier order, the all-candidates-in-one-call rule and the empty-candidates fallback
