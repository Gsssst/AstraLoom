## ADDED Requirements

### Requirement: LLM service captures reasoning content during streaming

The system SHALL provide `chat_stream_with_thinking` method that yields structured events with `type` field set to "reasoning" or "content". The `reasoning_content` from DeepSeek V4 Pro delta SHALL be captured and yielded as `{"type": "reasoning", "content": "..."}` events, separate from visible content events `{"type": "content", "content": "..."}`.

#### Scenario: Stream with thinking enabled

- **WHEN** caller invokes `chat_stream_with_thinking(messages)` with DeepSeek V4 Pro
- **THEN** the method SHALL yield reasoning events before content events
- **AND** each reasoning event SHALL have `type: "reasoning"`
- **AND** each content event SHALL have `type: "content"`

#### Scenario: Stream with thinking but model returns no reasoning

- **WHEN** model returns only content without reasoning_content in deltas
- **THEN** the method SHALL yield only `type: "content"` events
- **AND** SHALL NOT yield any `type: "reasoning"` events

### Requirement: API endpoints support show_thinking parameter

The SSE streaming endpoints for chat (`/api/chat/completions`, `/api/chat-sessions/{id}/send-stream`, `/api/papers/{id}/ask-stream`) SHALL accept optional `show_thinking` boolean parameter. When true, the endpoints SHALL use `chat_stream_with_thinking` and emit reasoning events as SSE event type "reasoning". When false or absent, endpoints SHALL use `chat_stream` and only emit content events.

#### Scenario: User enables thinking display in chat

- **WHEN** frontend sends `show_thinking: true` in stream request
- **THEN** SSE stream SHALL include `event: reasoning` frames with reasoning content
- **AND** SSE stream SHALL include `event: content` frames with visible content

#### Scenario: User disables thinking display (default)

- **WHEN** frontend sends `show_thinking: false` or omits the parameter
- **THEN** SSE stream SHALL only include `event: content` frames
- **AND** reasoning content SHALL NOT be transmitted

### Requirement: Frontend ThinkingPanel displays reasoning process

The system SHALL provide a ThinkingPanel component that renders the model's reasoning process. The panel SHALL be collapsed by default, showing a status indicator with elapsed time. When expanded, the panel SHALL display reasoning content in monospace font with muted styling. The panel SHALL auto-scroll to follow new reasoning text.

#### Scenario: Thinking panel shows collapsed by default

- **WHEN** reasoning events are received during a streaming response
- **THEN** the ThinkingPanel SHALL display "💭 思考中... (1.2s)" with a chevron icon
- **AND** the reasoning content SHALL be hidden

#### Scenario: User expands thinking panel

- **WHEN** user clicks the expand button on ThinkingPanel
- **THEN** the panel SHALL reveal the reasoning text in monospace gray font
- **AND** the text SHALL auto-scroll as new reasoning arrives

#### Scenario: Thinking completes and content begins

- **WHEN** the first content event arrives after reasoning events
- **THEN** the status indicator SHALL change to "💭 思考完成 (2.5s)"
- **AND** visible content SHALL render below the thinking panel
