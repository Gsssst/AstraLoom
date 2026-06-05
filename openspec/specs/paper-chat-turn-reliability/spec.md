# paper-chat-turn-reliability Specification

## Purpose
TBD - created by archiving change paper-chat-reliability-and-turn-controls. Update Purpose after archive.
## Requirements
### Requirement: Paper Q&A recovers visible answers from empty primary streams
The system SHALL attempt a stable concise-answer recovery stream when paper-detail Q&A primary generation ends without visible answer content.

#### Scenario: Reasoning-heavy primary stream has no visible answer
- **WHEN** paper-detail Q&A primary generation emits reasoning or ends without visible content
- **THEN** the system starts a stable recovery stream with an instruction to provide a concise final answer
- **AND** the system emits a status update before recovery begins

#### Scenario: Primary stream returns visible answer content
- **WHEN** paper-detail Q&A primary generation emits visible content
- **THEN** the system returns that content without running recovery

#### Scenario: Primary and recovery streams both fail
- **WHEN** neither paper-detail Q&A stream produces visible answer content
- **THEN** the system displays the existing empty-response warning

### Requirement: Thinking panels belong to individual answer turns
The system SHALL render reasoning content inside the corresponding assistant turn instead of a shared page-level panel.

#### Scenario: Multiple turns include reasoning
- **WHEN** a user completes multiple thinking-enabled questions
- **THEN** each assistant answer retains its own independent collapsible reasoning panel

#### Scenario: Visible content follows reasoning
- **WHEN** visible answer content begins after reasoning events
- **THEN** the corresponding turn changes its reasoning panel from streaming to complete

### Requirement: User can clear saved paper Q&A history
The system SHALL allow an authenticated user to clear saved Q&A history for one paper without removing other personal paper state.

#### Scenario: User confirms history clearing
- **WHEN** an authenticated user confirms clearing paper Q&A history
- **THEN** the system resets saved Q&A messages for that paper
- **AND** the frontend immediately returns to the empty paper-chat state

#### Scenario: User retains notes and saved state
- **WHEN** paper Q&A history is cleared
- **THEN** the system preserves the user's paper notes, reading state, tags, and collection state

