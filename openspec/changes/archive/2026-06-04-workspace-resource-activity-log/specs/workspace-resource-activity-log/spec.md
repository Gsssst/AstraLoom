# workspace-resource-activity-log Specification

## ADDED Requirements

### Requirement: Workspace resources are durably linked

The system SHALL allow workspace owners and editors to attach supported resources to a project space.

#### Scenario: Editor links paper

- **GIVEN** a workspace member with role `editor`
- **WHEN** they link a paper resource to the workspace
- **THEN** the resource appears in the workspace linked resource summary

#### Scenario: Viewer attempts to link resource

- **GIVEN** a workspace member with role `viewer`
- **WHEN** they attempt to link a resource
- **THEN** the request is rejected

### Requirement: Workspace activities are recorded

The system SHALL record workspace activity for lifecycle, member, and resource operations.

#### Scenario: Resource is linked

- **GIVEN** a user links a resource to a workspace
- **WHEN** the operation succeeds
- **THEN** an activity item records actor, action, resource type, resource id, and timestamp

### Requirement: Workspace detail exposes activity timeline

The frontend SHALL show recent workspace activity in the workspace detail page.

#### Scenario: User opens workspace detail

- **GIVEN** recent activity exists in a workspace
- **WHEN** a member opens the workspace detail page
- **THEN** the activity timeline is visible

### Requirement: Admin console exposes recent workspace activity

The admin console SHALL expose recent workspace activity for governance review.

#### Scenario: Admin opens console

- **GIVEN** workspace activity exists
- **WHEN** an administrator opens the admin console
- **THEN** recent workspace activity is visible
