## ADDED Requirements

### Requirement: Paper Q&A late stream interruptions do not pollute answers
The system SHALL distinguish paper-chat stream failures that happen after visible answer content from failures that happen before any visible content, and SHALL avoid appending late failure warnings into the answer body.

#### Scenario: Stream fails after answer content
- **WHEN** paper-detail Q&A has already emitted visible answer content
- **AND** the upstream stream fails before the normal done event
- **THEN** the frontend marks the assistant turn as possibly incomplete with a compact warning state
- **AND** the warning is not appended to the assistant answer content

#### Scenario: Stream fails before answer content
- **WHEN** paper-detail Q&A fails before emitting visible answer content
- **THEN** the existing visible failure fallback is shown as the answer content

#### Scenario: Interrupted answer is saved
- **WHEN** a partially generated answer is saved to chat history
- **THEN** the saved answer content excludes the late failure warning text
