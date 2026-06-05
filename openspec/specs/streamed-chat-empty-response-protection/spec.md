# streamed-chat-empty-response-protection Specification

## Purpose
TBD - created by archiving change streamed-chat-empty-response-protection. Update Purpose after archive.
## Requirements
### Requirement: Streamed chat never persists blank assistant replies
The chat system SHALL retry an empty streamed model response and SHALL persist a visible retryable message if no answer text is available after retry.

#### Scenario: Reasoning-only model stream
- **WHEN** the model emits reasoning output but no visible answer text
- **THEN** the backend retries the streamed request with a larger bounded output budget

#### Scenario: Empty stream after retry
- **WHEN** the model still emits no visible answer text after retry
- **THEN** the backend sends and persists a visible fallback message instead of an empty assistant message

### Requirement: Frontend preserves streamed answer frames
The chat frontend SHALL buffer partial SSE frames and preserve multiline model content.

#### Scenario: SSE frame crosses network chunks
- **WHEN** a JSON SSE frame arrives in multiple network chunks
- **THEN** the frontend reconstructs the complete event before appending its content

### Requirement: Chat request progress is visible
The chat frontend SHALL show a concise status label while retrieval and answer generation are in progress.

#### Scenario: Web-enhanced request is pending
- **WHEN** a user sends a message with web enhancement enabled
- **THEN** the chat message list displays a retrieval or generation progress label until the request finishes

