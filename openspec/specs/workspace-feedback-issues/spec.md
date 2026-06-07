# workspace-feedback-issues Specification

## Purpose
Define project-space feedback issue tracking so workspace members can submit, discuss, filter, and triage bugs, questions, ideas, tasks, and general feedback inside the project workflow.
## Requirements
### Requirement: Workspaces provide feedback issue tracking
The system SHALL allow authenticated workspace members to create, view, filter, and discuss feedback issues scoped to a project space.

#### Scenario: Member creates feedback issue
- **GIVEN** a user is a member of a project space
- **WHEN** they create an issue with title, description, type, priority, and optional labels
- **THEN** the issue is stored in that project space with status `open`
- **AND** the creator and creation timestamp are returned

#### Scenario: Non-member attempts to access issues
- **GIVEN** a user is not a member of a project space
- **WHEN** they list, create, view, update, or comment on workspace issues
- **THEN** the system rejects the request

#### Scenario: Member filters issues
- **GIVEN** a workspace has feedback issues with different statuses, types, priorities, and labels
- **WHEN** a member lists issues with filter parameters
- **THEN** the response includes only matching issues
- **AND** the response includes summary counts for open and closed issues

### Requirement: Workspace issue triage respects member roles
The system SHALL allow workspace owners and editors to triage issues while preserving viewer feedback submission.

#### Scenario: Viewer submits issue
- **GIVEN** a workspace member has role `viewer`
- **WHEN** they create an issue or add a comment
- **THEN** the operation succeeds

#### Scenario: Viewer attempts triage
- **GIVEN** a workspace member has role `viewer`
- **WHEN** they attempt to change issue status, priority, labels, assignee, or type
- **THEN** the request is rejected

#### Scenario: Editor closes issue
- **GIVEN** a workspace member has role `editor`
- **WHEN** they close an open issue
- **THEN** the issue status changes to `closed`
- **AND** closed timestamp and closer are recorded

### Requirement: Workspace issues preserve discussion history
The system SHALL allow workspace members to add comments to feedback issues and retrieve comments in chronological order.

#### Scenario: Member comments on issue
- **GIVEN** a workspace issue exists
- **WHEN** a workspace member adds a comment
- **THEN** the comment is stored with author and creation timestamp
- **AND** later issue detail requests include the comment

#### Scenario: Member opens issue detail
- **GIVEN** a workspace issue has comments
- **WHEN** a member opens issue detail
- **THEN** the response includes issue fields and comments ordered from oldest to newest

### Requirement: Workspace issue activity is recorded
The system SHALL record workspace activity for issue creation, triage, commenting, closing, and reopening.

#### Scenario: Issue lifecycle activity
- **WHEN** a workspace issue is created, updated, commented on, closed, or reopened
- **THEN** an activity item records actor, action, issue id, issue title, and timestamp

### Requirement: Project space UI exposes feedback issues
The frontend SHALL expose a compact GitHub Issues-style feedback section inside the project space detail page.

#### Scenario: User opens workspace detail
- **WHEN** a project space detail page renders
- **THEN** the page shows an issue section with open and closed counts, status/type/priority filters, and a create issue action

#### Scenario: User creates issue from workspace
- **WHEN** a member submits the issue form from the workspace detail page
- **THEN** the issue appears in the issue list without leaving the project space
- **AND** actionable error feedback is shown if creation fails

#### Scenario: User opens issue discussion
- **WHEN** a member selects an issue from the workspace issue list
- **THEN** the UI shows issue detail, comments, comment input, and status controls according to the user's role
