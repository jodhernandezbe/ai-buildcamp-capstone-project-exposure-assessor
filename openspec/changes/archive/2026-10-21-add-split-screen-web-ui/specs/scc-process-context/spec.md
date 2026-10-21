## MODIFIED Requirements

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
