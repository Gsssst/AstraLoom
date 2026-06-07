# notification-digest-center Specification

## Purpose
TBD - created by archiving change notification-digest-center. Update Purpose after archive.
## Requirements
### Requirement: Users can manage an in-app arXiv digest subscription
The system SHALL allow an authenticated user to save normalized arXiv digest keywords and enable or disable in-app digest notifications.

#### Scenario: Save a valid subscription
- **WHEN** an authenticated user saves at least one non-empty keyword and enables in-app notifications
- **THEN** the system persists the normalized keyword list and returns the current subscription state

#### Scenario: Reject an empty active subscription
- **WHEN** an authenticated user tries to enable in-app notifications without any non-empty keyword
- **THEN** the system rejects the update with a clear validation error

### Requirement: Users can trigger an immediate in-app test digest
The system SHALL allow an authenticated user with saved keywords to trigger a bounded immediate test delivery.

#### Scenario: Test push finds matching papers
- **WHEN** the user requests a test push and matching arXiv papers are returned
- **THEN** the system creates an unread in-app digest notification and returns the paper count and notification identifier

#### Scenario: Test push finds no matching papers
- **WHEN** the user requests a test push and no matching paper is returned
- **THEN** the system still creates an unread test notification that clearly reports the empty result

#### Scenario: Test push has no keywords
- **WHEN** the user requests a test push without saved keywords
- **THEN** the system rejects the request with a clear validation error

### Requirement: The system schedules daily in-app digests
The system SHALL load the digest Celery task and enqueue it from a single Celery Beat schedule each day.

#### Scenario: Scheduled delivery has matching papers
- **WHEN** the daily task processes an active in-app subscription with keywords and matching papers
- **THEN** the system creates an unread digest notification and updates the subscription last-delivery timestamp

#### Scenario: Scheduled delivery has no matching papers
- **WHEN** the daily task processes an active subscription but finds no matching papers
- **THEN** the system skips notification creation to avoid routine empty notifications

### Requirement: Email channel availability is explicit
The system MUST NOT present email digest delivery as operational until a mail transport is implemented.

#### Scenario: User views subscription settings
- **WHEN** the settings page loads the subscription state
- **THEN** the system reports email delivery as unavailable and the frontend displays the email control as disabled with an explanation

#### Scenario: User attempts to enable unavailable email delivery
- **WHEN** a client submits a subscription update with email delivery enabled
- **THEN** the system rejects the update with a clear validation error

### Requirement: Manual test feedback updates the visible notification state
The settings page SHALL display manual test progress and outcome, and a successful test SHALL refresh the global unread-notification badge without a page reload.

#### Scenario: Test notification succeeds
- **WHEN** a manual test creates an in-app notification
- **THEN** the settings page reports success, displays the returned delivery result, and refreshes the header unread badge

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

