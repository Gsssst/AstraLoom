## ADDED Requirements

### Requirement: GPT-compatible provider can stream reasoning summaries
The system SHALL use the OpenAI Responses API to stream reasoning summaries for the OpenAI-compatible provider when thinking display is requested.

#### Scenario: GPT thinking display is enabled
- **WHEN** the active provider is OpenAI-compatible
- **AND** the user sends a streamed chat message with thinking display enabled
- **THEN** the backend requests a streamed Responses API completion with reasoning summary enabled
- **AND** reasoning summary deltas are emitted to the frontend as `reasoning` stream events
- **AND** answer text deltas are emitted as `content` stream events

#### Scenario: GPT thinking display is disabled
- **WHEN** the active provider is OpenAI-compatible
- **AND** thinking display is disabled
- **THEN** the backend continues to use the existing Chat Completions streaming path

#### Scenario: Responses API returns unknown events
- **WHEN** the Responses stream includes events other than output text, reasoning summary, completion, or error events
- **THEN** the backend ignores those events without failing the chat turn

### Requirement: GPT thinking metadata reflects summary support
The chat stream metadata SHALL advertise GPT-compatible thinking support when the configured provider supports Responses API summaries.

#### Scenario: OpenAI-compatible provider is active
- **WHEN** stream metadata is emitted for an OpenAI-compatible provider
- **THEN** its capability metadata marks thinking support as available
