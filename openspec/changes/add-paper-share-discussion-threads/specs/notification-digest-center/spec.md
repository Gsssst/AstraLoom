## ADDED Requirements

### Requirement: Paper chat share discussion events create notifications
The system SHALL create in-app notifications for relevant paper chat share participants when discussion activity occurs.

#### Scenario: Share thread receives a new comment
- **WHEN** a participant comments on a paper chat share thread
- **THEN** the system creates unread in-app notifications for the other recorded participants except the commenting user
- **AND** each notification includes metadata needed to open the paper push center and locate the share thread

#### Scenario: Comment notification is opened
- **WHEN** a user opens a paper chat share discussion notification
- **THEN** the app navigates to the paper push center
- **AND** the referenced share can be expanded to show the discussion
