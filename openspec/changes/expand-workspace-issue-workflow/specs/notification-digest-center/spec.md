## ADDED Requirements

### Requirement: Workspace issue events create in-app notifications
The system SHALL create in-app notifications for relevant workspace members when feedback issue lifecycle events occur.

#### Scenario: Issue is created
- **GIVEN** a workspace issue is created by a member
- **WHEN** the creation succeeds
- **THEN** other workspace members receive an unread in-app notification with the issue title and workspace issue link

#### Scenario: Issue is commented on
- **GIVEN** a workspace issue receives a new comment
- **WHEN** the comment is stored
- **THEN** other workspace members receive an unread in-app notification with the issue title and workspace issue link

#### Scenario: Issue status changes
- **GIVEN** a workspace issue is closed or reopened
- **WHEN** the status change succeeds
- **THEN** other workspace members receive an unread in-app notification with the issue title, new status, and workspace issue link
