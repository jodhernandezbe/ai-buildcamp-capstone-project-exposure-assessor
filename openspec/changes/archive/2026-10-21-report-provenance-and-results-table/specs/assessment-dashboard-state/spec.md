## ADDED Requirements

### Requirement: The chemical carries its name
The workspace's chemical SHALL carry the preferred name the properties result gave (None when it gave none), with its source among the chemical's sources, taken only from that result.

#### Scenario: Name reported
- **WHEN** a properties result with a preferred name is projected
- **THEN** the chemical shows that name and its source

#### Scenario: Name absent
- **WHEN** the properties result has no name
- **THEN** the chemical's name is None and nothing else fills it
