## ADDED Requirements

### Requirement: The industry must be given in words
The SCC process lookup SHALL search with the industry's name in words. It SHALL drop numeric NAICS codes (and the label words "NAICS" and "code" written beside a number) from the description before searching, and SHALL refuse a description that contains nothing but a code, with no search and a warning that says a code means nothing to a text search and that the NAICS title is needed. Its description SHALL state that the numeric code alone must never be passed, where the title comes from, and that when nothing useful is returned the SCC-based stack tool is called without a code for the EPA global default.

#### Scenario: Bare code
- **WHEN** the description is "324110" or "NAICS code 324-110"
- **THEN** no search is made, no matches are returned and a warning asks for the industry's name in words

#### Scenario: Code beside the title
- **WHEN** the description is "324110 Petroleum Refineries"
- **THEN** the search uses "Petroleum Refineries"

#### Scenario: Digits inside a word
- **WHEN** the description is "3D Printing Services"
- **THEN** it is searched as given
