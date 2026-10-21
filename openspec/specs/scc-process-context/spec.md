# scc-process-context Specification

## Purpose

Lets the agent turn a NAICS industry description into the matching EPA Source Classification Codes and their plain-text process descriptions, so the LLM understands which physical process it is evaluating and has an SCC for the tier 2 stack lookup.

## Requirements

### Requirement: SCC retrieval from a NAICS description
The system SHALL provide a tool that, given a NAICS description, returns up to a configured number of best-matching SCC entries, ranked by semantic similarity. Each entry SHALL include the SCC code, SCC level one, two, three and four descriptions, the EPA emission sector, and a similarity score. The level four description SHALL always be present on returned entries.

#### Scenario: Matching industry
- **WHEN** the tool is called with "Petroleum Refineries"
- **THEN** it returns entries ranked best first, each with SCC code, all four level descriptions, sector and score

#### Scenario: Result count bound
- **WHEN** the configured top-k is 5
- **THEN** at most 5 entries are returned

#### Scenario: Empty description
- **WHEN** the description is empty or whitespace
- **THEN** it returns an empty list with a warning, and no embedding request is made

### Requirement: Indexed SCC scope
The index SHALL contain only SCC rows of the source table whose data category is "Point" and whose status is "Active". Rows without an SCC code or level four description SHALL be excluded. Each SCC code SHALL appear in the index at most once.

#### Scenario: Retired and non-point codes excluded
- **WHEN** the index is built
- **THEN** no returned entry ever has a retired status or a data category other than Point

#### Scenario: Duplicate SCC rows
- **WHEN** the source table lists an SCC twice
- **THEN** the index holds one entry for it

### Requirement: Persistent, rebuildable index
The index SHALL be persisted on disk and reused across runs. It SHALL be built from the source table on first use when absent, and SHALL be rebuilt when the source table or the indexing configuration changes. Building SHALL NOT happen on every query.

#### Scenario: First use
- **WHEN** the tool is called and no persisted index exists
- **THEN** the index is built, persisted and then queried

#### Scenario: Source table changed
- **WHEN** the source table's content differs from the one the persisted index was built from
- **THEN** the index is rebuilt before querying

### Requirement: Provider-agnostic embeddings
Embedding SHALL go through a replaceable embeddings interface. The default provider SHALL be OpenAI embeddings with the model named in configuration. The tool SHALL NOT call a chat or completion model. The embeddings SHALL use the provider key made available to the current request when there is one (the web program supplies the key stored in the OS keychain for the duration of a turn), and otherwise the key in the configured environment variable. The embeddings and the cached retriever SHALL NOT hold a key between calls: the key SHALL be resolved afresh for every embedding request.

#### Scenario: Injected embedder
- **WHEN** a different embeddings implementation is supplied
- **THEN** the index and queries use it with no other code change

#### Scenario: Request key preferred
- **WHEN** a request key is available and the environment variable is also set
- **THEN** the embedding request uses the request key

#### Scenario: Key not retained
- **WHEN** an embedding request has been made under one request key and a later one under another
- **THEN** each request uses its own key, and with neither a request key nor the environment variable the later request fails with an error naming the variable

#### Scenario: Environment fallback
- **WHEN** no request key is available and the environment variable is set
- **THEN** the embedding request uses the environment variable's key

### Requirement: Fail closed on retrieval errors
Missing API credentials, embedding-service errors, timeouts and an unreadable source table SHALL NOT raise into the agent; the tool SHALL return an empty list with a warning that names the cause. Setup errors in configuration SHALL raise at load time.

#### Scenario: Embedding service unavailable
- **WHEN** the embedding call fails or times out
- **THEN** the tool returns an empty list with a warning and does not retry indefinitely

#### Scenario: Missing API key
- **WHEN** the configured API-key environment variable is unset
- **THEN** the tool returns an empty list with a warning naming the variable

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
