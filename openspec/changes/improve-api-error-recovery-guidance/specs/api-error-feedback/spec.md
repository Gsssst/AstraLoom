## MODIFIED Requirements

### Requirement: API failures produce clear user feedback
The frontend SHALL translate API, timeout, network, validation, authentication, and permission failures into concise Chinese user-facing messages and structured recovery details instead of generic "失败" text or silent no-ops.

#### Scenario: Backend returns a structured app error
- **WHEN** a frontend action receives an API response containing an app error envelope with a message
- **THEN** the UI displays that message with the action context preserved

#### Scenario: Backend returns validation details
- **WHEN** a frontend action receives FastAPI validation detail data
- **THEN** the UI displays the first relevant validation message rather than raw JSON

#### Scenario: Request times out or loses network
- **WHEN** a frontend action fails because the request timed out or no response was received
- **THEN** the UI displays a recoverable network message that indicates the user can retry

#### Scenario: Page needs persistent recovery guidance
- **WHEN** a page requests structured API error details
- **THEN** the helper returns a message, severity, category, retryability flag, and suggested recovery action.

### Requirement: High-frequency workflows use shared error parsing
The frontend SHALL use a shared error parsing helper in high-frequency chat, paper library, research direction, and settings workflows.

#### Scenario: User action fails on a high-frequency page
- **WHEN** an action such as loading, searching, deleting, saving, uploading, or switching settings fails
- **THEN** the page displays a specific message derived through the shared parser with an action-specific fallback

#### Scenario: Streaming chat reports an error
- **WHEN** the chat stream emits an error event or ends with an error payload
- **THEN** the chat page surfaces the error as a visible assistant/error message and resets the sending state

#### Scenario: Model connection test fails
- **WHEN** the settings API connection test fails
- **THEN** the settings page displays persistent recovery guidance derived from the shared error parser.
