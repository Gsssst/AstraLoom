## MODIFIED Requirements

### Requirement: Streaming chat respects manual scroll position
The chat message list SHALL not force-scroll to the bottom while the user is reading earlier generated content during streaming.

#### Scenario: User scrolls upward while answer streams
- **WHEN** an answer is streaming
- **AND** the user scrolls upward or otherwise moves away from the bottom
- **THEN** subsequent streamed chunks do not force the list back to the bottom.

#### Scenario: User returns to bottom
- **WHEN** the user scrolls back near the bottom
- **THEN** subsequent streamed chunks may continue bottom-following.
