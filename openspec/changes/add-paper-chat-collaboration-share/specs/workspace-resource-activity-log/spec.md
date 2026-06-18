## ADDED Requirements

### Requirement: Workspace activities include shared paper AI insights
The system SHALL record a workspace activity when a member shares a paper AI reading insight to the project space.

#### Scenario: Paper chat insight is shared
- **GIVEN** a paper chat answer is shared to a linked project space
- **WHEN** the share operation succeeds
- **THEN** the workspace activity timeline includes an item with action `paper_chat_shared`, resource type `papers`, the paper id, and metadata describing the shared question and paper title

#### Scenario: Workspace assistant uses activity context
- **GIVEN** a workspace has recent `paper_chat_shared` activities
- **WHEN** the workspace assistant builds recent activity context
- **THEN** the shared insight activity can be included like other workspace activities
