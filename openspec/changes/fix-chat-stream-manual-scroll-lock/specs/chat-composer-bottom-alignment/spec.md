## ADDED Requirements

### Requirement: Streaming chat preserves manual scroll position
The chat interface SHALL stop following the bottom while an answer is streaming when the user manually scrolls away from the bottom.

#### Scenario: User scrolls up during generation
- **WHEN** an assistant answer is streaming
- **AND** the user scrolls upward or otherwise moves the chat container away from the bottom
- **THEN** subsequent streamed chunks do not force the chat container back to the bottom.

#### Scenario: User returns to bottom
- **WHEN** the user scrolls back near the bottom of the chat container
- **THEN** streaming output may resume following the bottom.

#### Scenario: User sends a new message
- **WHEN** the user sends a new chat message
- **THEN** follow-output is re-enabled for the new turn so the prompt and initial response are visible.
