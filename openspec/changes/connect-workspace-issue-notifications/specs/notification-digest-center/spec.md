## ADDED Requirements

### Requirement: Global notifications route workspace issue events
The system SHALL expose workspace issue notifications as actionable global notifications that can be read, filtered, and opened from the app header.

#### Scenario: User filters workspace issue notifications
- **WHEN** an authenticated user requests notifications with category `workspace_issue`
- **THEN** the response contains only that user's workspace issue notifications
- **AND** each response item includes notification metadata needed to open the workspace issue link

#### Scenario: User opens workspace issue notification
- **WHEN** a user clicks a workspace issue notification in the global header popover
- **THEN** the notification is marked read
- **AND** the app navigates to the workspace issue path from notification metadata

#### Scenario: Workspace issue notification lacks explicit path
- **WHEN** a workspace issue notification has workspace and issue identifiers but no explicit path
- **THEN** the frontend derives `/workspaces/<workspace_id>?issue=<issue_id>` and navigates there

### Requirement: Users can mark visible notifications read from the header
The system SHALL let authenticated users mark all visible in-app notifications read without breaking digest-specific read behavior.

#### Scenario: User marks header notifications read
- **WHEN** the user chooses the header popover mark-all-read action
- **THEN** unread notifications in the current list scope are marked read
- **AND** the global unread badge refreshes without a full page reload

#### Scenario: Digest read-all endpoint remains scoped
- **WHEN** the paper digest inbox marks digest notifications read
- **THEN** only digest notifications are marked read
- **AND** unrelated workspace issue notifications remain unread
