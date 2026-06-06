## ADDED Requirements

### Requirement: Regeneration actions send deterministic prompts
Chat regeneration menu actions SHALL send their intended prompt without depending on asynchronous input state updates.

#### Scenario: User chooses a regeneration mode
- **WHEN** a user clicks an assistant message regeneration action
- **THEN** the chat sends the prompt associated with that action directly
- **AND** it does not depend on `setInput()` completing before `handleSend()`

#### Scenario: User sends from the composer
- **WHEN** a user presses Enter or clicks the normal send button
- **THEN** the chat continues to send the current composer text and then clears the composer

#### Scenario: Empty explicit prompt is requested
- **WHEN** a programmatic send receives no usable prompt text
- **THEN** the chat does not send an empty request
