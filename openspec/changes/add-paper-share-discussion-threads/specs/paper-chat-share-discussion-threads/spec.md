## ADDED Requirements

### Requirement: Paper chat shares have discussion threads
The system SHALL attach a discussion thread to each paper chat share so senders and recipients can discuss the shared AI reading insight.

#### Scenario: New share creates a shared thread
- **WHEN** a user shares selected paper AI chat messages to one or more users
- **THEN** the system stores a stable share thread identifier shared by all recipient notifications for that share
- **AND** the sender and recipients are recorded as participants

#### Scenario: Existing share lacks a thread identifier
- **WHEN** a user opens an older paper chat share notification without a thread identifier
- **THEN** the system treats the notification as a legacy single-notification thread
- **AND** the share content remains readable

### Requirement: Participants can comment on paper chat share threads
The system SHALL allow authorized share participants to add and read chronological comments on a paper chat share thread.

#### Scenario: Recipient adds a comment
- **WHEN** a recipient posts a non-empty comment on a share thread they can access
- **THEN** the system stores the comment with author identity and timestamp
- **AND** subsequent thread reads include the new comment in chronological order

#### Scenario: Unauthorized user requests a thread
- **WHEN** a user who is not a sender, recipient, or participant requests a share thread
- **THEN** the system rejects access without exposing thread content

#### Scenario: Empty comment is submitted
- **WHEN** a participant submits an empty or whitespace-only comment
- **THEN** the system rejects the request with a validation error

### Requirement: Users can triage shared reading insights
The system SHALL let each participant mark a paper chat share as useful, follow-up needed, or resolved without changing other users' status.

#### Scenario: User marks a share useful
- **WHEN** a participant marks a share as useful
- **THEN** the system persists that user's status for the share thread
- **AND** the paper push center reflects the status on that share card

#### Scenario: User clears a share status
- **WHEN** a participant clears their status
- **THEN** the system removes that user's status for the share thread
- **AND** other participants' statuses remain unchanged
