# admin-workspace-governance Specification

## Purpose
Define the administrator governance surface for inspecting system health, managing user roles, and monitoring project-space membership without exposing these controls to regular users.
## Requirements
### Requirement: Admins can inspect system governance state

The system SHALL expose admin-only overview data for users and project spaces.

#### Scenario: Admin opens overview

- **GIVEN** an authenticated administrator
- **WHEN** they request the admin overview
- **THEN** the response includes user, admin, active-user, paper, writing-project, and workspace counts

#### Scenario: Regular user requests overview

- **GIVEN** an authenticated non-admin user
- **WHEN** they request the admin overview
- **THEN** the request is rejected

### Requirement: Admins can manage user roles and activation

The system SHALL allow administrators to update user roles and active state with safety guards.

#### Scenario: Admin promotes user

- **GIVEN** an authenticated administrator
- **WHEN** they update a user role to `admin`
- **THEN** the user role is updated

#### Scenario: Admin attempts unsafe self change

- **GIVEN** an authenticated administrator
- **WHEN** they attempt to deactivate themselves or remove the last admin
- **THEN** the request is rejected

### Requirement: Admins can inspect project spaces

The system SHALL expose project-space ownership and membership visibility for administrators.

#### Scenario: Admin lists project spaces

- **GIVEN** project spaces exist
- **WHEN** an administrator lists workspaces
- **THEN** each row includes owner, status, member count, and role breakdown

### Requirement: Frontend exposes admin console

The frontend SHALL expose an admin-only console entry.

#### Scenario: Admin sees admin navigation

- **GIVEN** the current user role is `admin`
- **WHEN** the app layout renders
- **THEN** the sidebar includes an admin console entry
