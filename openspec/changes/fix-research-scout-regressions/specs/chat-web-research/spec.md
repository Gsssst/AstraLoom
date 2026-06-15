## MODIFIED Requirements

### Requirement: Displayed sources reflect the active retrieval mode
The chat UI SHALL distinguish ordinary web retrieval sources from Research Scout scholarly candidate sources.

#### Scenario: Ordinary web retrieval produces sources
- **WHEN** ordinary chat uses web retrieval
- **THEN** the source strip is labeled as retrieved sources
- **AND** each source includes provider/query metadata when available.

#### Scenario: Research Scout produces paper candidates
- **WHEN** Research Scout produces paper candidates
- **THEN** the source strip is labeled as paper candidate sources
- **AND** generic web references are not shown for that assistant message.
