## ADDED Requirements

### Requirement: Chat streaming respects manual scroll position
The chat workspace SHALL preserve user-controlled reading position during streamed answer generation.

#### Scenario: User reads earlier generated content
- **WHEN** a chat answer is streaming and the user scrolls the message list away from the bottom
- **THEN** new streamed content does not force the message list back to the bottom

#### Scenario: User returns to latest output
- **WHEN** the user scrolls back near the bottom of the chat message list
- **THEN** subsequent streamed content follows the latest output automatically
