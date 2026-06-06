## ADDED Requirements

### Requirement: Chat users can stop active stream generation
The chat page SHALL provide a stop control while an assistant response is streaming.

#### Scenario: User stops a streaming reply
- **WHEN** a user clicks the stop control during a streamed chat response
- **THEN** the frontend aborts the active stream request
- **AND** the chat composer returns to a send-ready state
- **AND** any already streamed assistant content remains visible

#### Scenario: Cancellation is not shown as a model failure
- **WHEN** a user stops a streamed chat response
- **THEN** the page does not append a generic model error message for the abort
- **AND** transient stream timing/status state is reset

#### Scenario: No stream is active
- **WHEN** no message is currently sending
- **THEN** the stop control is not presented as an available action
