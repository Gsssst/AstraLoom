## ADDED Requirements

### Requirement: Paper chat shares can target arbitrary active users
The system SHALL let an authenticated user send a paper AI chat excerpt to selected active users without requiring a linked project space.

#### Scenario: User searches share recipients
- **GIVEN** the requester is authenticated
- **WHEN** the requester searches paper chat share recipients by username, display name, or email
- **THEN** the system returns active user candidates excluding the requester

#### Scenario: User shares to selected users
- **GIVEN** the requester is authenticated and the source paper exists
- **AND** the request includes one or more valid recipient user ids
- **WHEN** the requester submits a paper chat share
- **THEN** each selected recipient receives a `paper_chat_share` notification
- **AND** the notification metadata identifies the source paper, sender, selected messages, optional note, and source path

#### Scenario: Request includes invalid recipients
- **GIVEN** the requester submits recipient user ids that are inactive, missing, or the requester's own id
- **WHEN** the share request is validated
- **THEN** the system rejects the request without creating partial notifications

### Requirement: Paper chat shares contain selected conversation messages
The system SHALL let the sender share a curated set of selected paper chat messages instead of only one assistant answer.

#### Scenario: Sender selects multiple messages
- **GIVEN** a paper chat conversation contains user and assistant messages
- **WHEN** the sender enters share-selection mode and selects multiple messages
- **THEN** the share modal previews the selected messages with role and content excerpts

#### Scenario: Sender uses assistant answer shortcut
- **GIVEN** an assistant answer has finished streaming
- **WHEN** the sender clicks the share shortcut on that answer
- **THEN** the system preselects the assistant answer and the nearest earlier user question

#### Scenario: Selected content exceeds bounds
- **GIVEN** selected messages or references exceed storage bounds
- **WHEN** the share is persisted
- **THEN** the system stores bounded message content, excerpts, and references safe for notification rendering

#### Scenario: Sender submits no selected messages
- **GIVEN** the sender has not selected any paper chat messages
- **WHEN** the sender tries to submit a share
- **THEN** the frontend prevents submission and the backend rejects an empty selected-message payload
