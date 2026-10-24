## ADDED Requirements

### Requirement: A category match is disclosed and reasoned about
The prompt SHALL explain, as assessment reasoning and without naming a tool, that TRI reports
some chemicals only as members of a category rather than under their own CAS number. It SHALL
say that when a chemical is found in a category, the assessor tells the user plainly that the
chemical was matched through that category, names the category, and explains that the
reported releases cover every member of the category together, so they are an upper bound on
what that one chemical contributes and not a measured release of it. It SHALL say that a
category match is tried before an analogue is sought, and that an analogue is sought only
when the chemical is in no category; and that the chemical's own toxicity benchmark is still
required and is not taken from the category.

#### Scenario: Category match
- **WHEN** the prompt is read
- **THEN** it says the user is told when a category stood in for a chemical, and that category releases cover all members

#### Scenario: Order of fallbacks
- **WHEN** the prompt is read
- **THEN** it says a category is checked before an analogue is sought

#### Scenario: Prompt names no tool
- **WHEN** the prompt is read
- **THEN** it names no tool and no call order
