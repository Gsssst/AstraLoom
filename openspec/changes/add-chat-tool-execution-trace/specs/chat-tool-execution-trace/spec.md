## ADDED Requirements

### Requirement: Chat streams tool execution trace metadata
Chat streamed responses SHALL be able to include a structured `tool_trace` payload describing tools used during the assistant turn.

#### Scenario: Assistant runs a research workflow
- **WHEN** a chat request triggers a workflow such as Research Scout
- **THEN** the stream metadata includes ordered tool trace steps
- **AND** each step includes an id, tool name, label, status, summary, and optional detail fields.

#### Scenario: A tool has side effects
- **WHEN** a tool would mutate library, folder, project, or files
- **THEN** the trace marks it as waiting for user action or available
- **AND** the backend does not run the side effect without an explicit user request.

### Requirement: Chat renders tool execution traces
The chat interface SHALL display tool execution steps near the assistant answer when trace metadata is present.

#### Scenario: Tool trace exists on a message
- **WHEN** an assistant message has `tool_trace.steps`
- **THEN** the UI renders a compact execution trace with status, tool label, and summary
- **AND** the trace remains visually connected to the assistant answer and Research Scout cards.

#### Scenario: Tool trace is absent
- **WHEN** a normal assistant message does not include tool trace metadata
- **THEN** the chat UI behaves as before without an empty trace panel.
