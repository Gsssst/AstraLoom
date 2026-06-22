## MODIFIED Requirements

### Requirement: Paper chat turns recover from empty model streams
The paper-detail chat stream SHALL avoid ending with no visible answer when a non-streaming stable answer can be produced from the same context.

#### Scenario: Streaming recovery falls back to non-streaming answer
- **WHEN** the primary paper chat stream emits no visible content
- **AND** the recovery stream also emits no visible content
- **AND** a non-streaming stable answer returns text
- **THEN** the stream emits that text as answer content
- **AND** the final empty-response warning is not shown

#### Scenario: All model attempts return no visible content
- **WHEN** the primary stream, recovery stream, and non-streaming stable fallback all return no visible content
- **THEN** the stream MAY show the existing empty-response warning
- **AND** the stream still completes cleanly
