# Capability: Paper Reading Workflow

## ADDED Requirements

### Requirement: Reading Queue Status Counts

The system SHALL provide per-user counts for papers in each reading status.

#### Scenario: User views reading queue counts

- **GIVEN** the user has papers marked as `unread`, `reading`, and `completed`
- **WHEN** the frontend requests reading status counts
- **THEN** the response includes all three statuses
- **AND** missing statuses are returned as zero

### Requirement: Reading Queue Filtering

The paper library SHALL let authenticated users filter their reading list by status.

#### Scenario: User filters reading list

- **GIVEN** the user is on the paper library page
- **WHEN** the user selects the reading list source and chooses `阅读中`
- **THEN** only papers with `read_status = "reading"` are requested and displayed

### Requirement: Quick Reading Status Updates

The paper library SHALL let users update reading status directly from paper cards.

#### Scenario: User starts reading a paper

- **GIVEN** a paper appears in the user's unread queue
- **WHEN** the user clicks `开始阅读`
- **THEN** the paper status is updated to `reading`
- **AND** the queue counts refresh
- **AND** the paper leaves the unread-filtered list

### Requirement: Detail Page Reading Status Control

The paper detail page SHALL show and persist the current user's reading status for that paper.

#### Scenario: User marks detail page paper completed

- **GIVEN** the user is viewing a paper detail page
- **WHEN** the user changes reading status to `已完成`
- **THEN** the status is persisted
- **AND** notes, saved state, and chat history are not cleared

### Requirement: Existing Personal Paper State Compatibility

Updating reading status SHALL preserve existing user paper fields.

#### Scenario: User updates status after taking notes

- **GIVEN** a user has saved notes and chat history for a paper
- **WHEN** the user updates the paper read status
- **THEN** the system updates only the reading status and saved flag as needed
- **AND** notes, personal tags, and paper chat history remain unchanged
