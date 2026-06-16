## ADDED Requirements

### Requirement: Paper chat streamed answers can be stopped
The paper-detail chat UI SHALL allow users to stop an in-flight streamed answer and return the composer to an editable state.

#### Scenario: User stops a paper chat stream
- **WHEN** a paper-detail AI answer is streaming
- **AND** the user activates the stop control
- **THEN** the current request is aborted
- **AND** the partial assistant message is finalized instead of continuing to append content
- **AND** the input controls become usable again

#### Scenario: Stream abort is user requested
- **WHEN** a paper-detail stream is aborted by the stop control
- **THEN** the UI does not append a generic failure message for that user-requested abort
