## ADDED Requirements

### Requirement: Tool traces are compact by default
The chat workspace SHALL render tool execution traces in a collapsed summary state by default while preserving access to the full step list.

#### Scenario: Assistant message has tool trace
- **WHEN** an assistant message includes tool trace metadata
- **THEN** the page shows a compact trace summary with workflow, step count, stop reason when available, and the latest meaningful step status
- **AND** the full step list is hidden by default.

#### Scenario: User expands tool trace
- **WHEN** the user activates the trace expand control
- **THEN** the full tool step list appears in place
- **AND** the user can collapse it again without affecting Research Scout candidate cards or message content.
