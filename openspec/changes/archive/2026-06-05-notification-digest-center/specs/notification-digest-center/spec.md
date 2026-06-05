## ADDED Requirements

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
