## ADDED Requirements

### Requirement: Assistant mode coordinates with retrieval controls
Chat requests SHALL submit an assistant mode without disabling existing knowledge-base, web, depth, thinking, or attachment controls.

#### Scenario: Research Scout with knowledge base and web enabled
- **WHEN** a user sends a Research Scout request while knowledge-base retrieval and web enhancement are enabled
- **THEN** the request preserves those retrieval settings
- **AND** the backend uses Research Scout scholarly discovery in addition to the available chat context.

#### Scenario: Invalid assistant mode is submitted
- **WHEN** a chat request contains an unsupported assistant mode
- **THEN** request validation rejects the payload.
