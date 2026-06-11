## MODIFIED Requirements

### Requirement: Admins can inspect project spaces
The system SHALL expose project-space ownership, membership, resources, issues, activities, and dashboard visibility for administrators.

#### Scenario: Admin lists project spaces
- **GIVEN** an authenticated administrator
- **AND** project spaces exist
- **WHEN** an administrator lists workspaces
- **THEN** the response includes owner, member count, and role distribution for each active project space

#### Scenario: Admin opens workspace content
- **GIVEN** an authenticated administrator
- **AND** a project space exists
- **WHEN** the administrator requests that workspace's admin detail
- **THEN** the response includes members, linked resources, dashboard summary, open issue summary, and recent activities

#### Scenario: Non-admin opens workspace content through admin API
- **GIVEN** an authenticated non-admin user
- **WHEN** they request a workspace through the admin detail API
- **THEN** the system rejects the request
