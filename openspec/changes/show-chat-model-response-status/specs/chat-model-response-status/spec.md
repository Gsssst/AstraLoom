## ADDED Requirements

### Requirement: Stream exposes safe model status metadata
The streaming chat API SHALL include display-safe active model metadata in the stream `meta` event.

#### Scenario: Stream metadata includes active model identity
- **WHEN** a user sends a streamed chat message
- **THEN** the `meta` event includes provider, display label, model id, and capability flags for the selected model
- **AND** the metadata does not include API keys or API base URLs

### Requirement: Chat toolbar shows active model and capabilities
The chat page SHALL show the active model identity and active capability modes near the chat controls.

#### Scenario: Model metadata is available
- **WHEN** stream metadata has been received for the current or most recent turn
- **THEN** the chat toolbar shows the model label or model id
- **AND** it indicates knowledge-base retrieval, web search, thinking, and vision support states

#### Scenario: Model metadata is not yet available
- **WHEN** the chat page has not received model metadata yet
- **THEN** the chat toolbar shows a neutral current-model placeholder without blocking the chat

### Requirement: Streaming status distinguishes waiting and generating
The chat page SHALL distinguish request/retrieval progress, waiting for the first model token, and active generation.

#### Scenario: Message is waiting for the first token
- **WHEN** the user sends a message and no content or reasoning token has arrived
- **THEN** the sending indicator shows that the system is waiting for the model's first response segment with elapsed time

#### Scenario: Message is streaming content
- **WHEN** content or reasoning tokens have started arriving
- **THEN** the sending indicator shows active generation with elapsed time

#### Scenario: Message completes or errors
- **WHEN** the stream finishes or an error is surfaced
- **THEN** transient timing state resets and the completed message remains in the conversation
