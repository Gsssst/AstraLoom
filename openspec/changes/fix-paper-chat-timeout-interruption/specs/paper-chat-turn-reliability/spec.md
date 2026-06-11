## MODIFIED Requirements

### Requirement: Paper Q&A recovers visible answers from empty primary streams
The system SHALL attempt a stable concise-answer recovery stream when paper-detail Q&A primary generation ends or stalls without visible answer content, and SHALL NOT interrupt a thinking-enabled primary stream solely because the total generation time exceeds the first-visible-answer guard after visible content has started.

#### Scenario: Reasoning-heavy primary stream has no visible answer
- **WHEN** paper-detail Q&A primary generation emits reasoning or stalls without visible content
- **THEN** the system starts a stable recovery stream with an instruction to provide a concise final answer
- **AND** the system emits a status update before recovery begins

#### Scenario: Primary stream returns visible answer content
- **WHEN** paper-detail Q&A primary generation emits visible content
- **THEN** the system returns that content without running recovery

#### Scenario: Thinking stream continues after first visible answer guard
- **WHEN** paper-detail Q&A uses thinking mode
- **AND** the primary stream has emitted visible answer content
- **AND** the overall stream duration exceeds the first-visible-answer guard
- **THEN** the system continues streaming answer content instead of sending an interruption warning

#### Scenario: Primary and recovery streams both fail
- **WHEN** neither paper-detail Q&A stream produces visible answer content
- **THEN** the system displays the existing empty-response warning
