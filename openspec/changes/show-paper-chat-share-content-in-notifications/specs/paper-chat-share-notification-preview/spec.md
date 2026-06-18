## ADDED Requirements

### Requirement: Paper chat share notifications preview shared content
The system SHALL render selected paper chat share content directly inside the global notification popover.

#### Scenario: Recipient sees selected messages in notification center
- **GIVEN** a `paper_chat_share` notification contains selected paper chat messages
- **WHEN** the recipient opens the notification popover
- **THEN** the notification card displays the sender, paper title, optional note, and selected message excerpts

#### Scenario: Recipient opens source paper from preview
- **GIVEN** a paper chat share preview is visible in the notification popover
- **WHEN** the recipient clicks the open-paper action
- **THEN** the notification is marked read
- **AND** the app navigates to the paper path from notification metadata

### Requirement: Sender can broadcast a paper chat share to all active users
The system SHALL let the sender choose all active users as recipients for a paper chat share.

#### Scenario: Sender selects all users in share modal
- **GIVEN** the sender is in the paper chat share modal
- **WHEN** the sender clicks the all-users action
- **THEN** the modal selects broadcast mode and the share request includes `all_users: true`

#### Scenario: Backend resolves all active recipients
- **GIVEN** a share request includes `all_users: true`
- **WHEN** the backend creates notifications
- **THEN** every active user except the sender receives the paper chat share notification
