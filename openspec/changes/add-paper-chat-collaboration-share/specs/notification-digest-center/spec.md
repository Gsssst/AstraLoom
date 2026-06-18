## ADDED Requirements

### Requirement: Global notifications route paper chat share events
The system SHALL expose paper chat collaboration share notifications as actionable global notifications.

#### Scenario: User filters paper chat share notifications
- **WHEN** an authenticated user requests notifications with category `paper_chat_share`
- **THEN** the response contains only that user's paper chat share notifications
- **AND** each response item includes metadata needed to open the source paper

#### Scenario: User opens paper chat share notification
- **WHEN** a user clicks a paper chat share notification in the global header popover
- **THEN** the notification is marked read
- **AND** the app navigates to the source paper path from notification metadata

#### Scenario: Paper chat share notification lacks explicit path
- **WHEN** a paper chat share notification has a paper identifier but no explicit path
- **THEN** the frontend derives `/papers/<paper_id>` and navigates there
