## ADDED Requirements

### Requirement: Paper chat share notifications include multi-message excerpts
The system SHALL expose direct paper chat shares as actionable notifications containing the selected conversation excerpt.

#### Scenario: Recipient opens direct paper chat share notification
- **WHEN** a recipient clicks a `paper_chat_share` notification
- **THEN** the notification is marked read
- **AND** the app navigates to the source paper path from notification metadata

#### Scenario: Notification metadata includes selected messages
- **WHEN** a direct paper chat share notification is created
- **THEN** its metadata includes `selected_messages`, `message_count`, `sender_id`, `sender_name`, `paper_id`, `paper_title`, and `path`

#### Scenario: Notification lacks explicit path
- **WHEN** a `paper_chat_share` notification has a paper identifier but no explicit path
- **THEN** the frontend derives `/papers/<paper_id>` and navigates there
