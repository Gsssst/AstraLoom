## ADDED Requirements

### Requirement: Paper chat streaming respects manual scroll position
The paper-detail AI Q&A panel SHALL preserve user-controlled reading position during streamed answer generation.

#### Scenario: User reads earlier paper answer content
- **WHEN** a paper-detail AI answer is streaming and the user scrolls the chat message list away from the bottom
- **THEN** new streamed content does not force the chat message list back to the bottom

#### Scenario: User returns to latest paper answer output
- **WHEN** the user scrolls back near the bottom of the paper-detail chat message list
- **THEN** subsequent streamed content follows the latest output automatically
