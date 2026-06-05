## ADDED Requirements

### Requirement: Private research workspaces are owner-scoped
The system SHALL require authentication for private research workspace operations and SHALL only return or mutate projects, ideas, experiments, and project share links owned by the current user.

#### Scenario: User lists research projects
- **WHEN** an authenticated user requests their research projects
- **THEN** the system returns only projects whose owner matches the current user

#### Scenario: User accesses another user's research project
- **WHEN** an authenticated user requests or mutates a project or idea owned by another user
- **THEN** the system returns `404` without disclosing the private resource

#### Scenario: User creates a share link
- **WHEN** an authenticated project owner requests a share link
- **THEN** the system creates a token for that owned project

#### Scenario: Visitor opens a shared project
- **WHEN** a visitor presents a valid project share token
- **THEN** the system returns the public read-only shared payload without requiring authentication

### Requirement: Personal folders are owner-scoped
The system SHALL require authentication for folder operations and SHALL only list, nest, or delete folders owned by the current user.

#### Scenario: User lists folders
- **WHEN** an authenticated user requests the folder tree
- **THEN** the system returns only root folders owned by the current user

#### Scenario: User creates a nested folder under another user's parent
- **WHEN** an authenticated user supplies a parent folder owned by another user
- **THEN** the system returns `404` and does not create the folder

#### Scenario: User deletes another user's folder
- **WHEN** an authenticated user requests deletion of a folder owned by another user
- **THEN** the system returns `404` and preserves the folder

### Requirement: Cross-user statistics are administrator-only
The system SHALL restrict system-wide usage summaries and dashboard data to administrators, and SHALL return only the current user's usage history to ordinary users.

#### Scenario: Ordinary user requests all-user usage summary
- **WHEN** an authenticated ordinary user requests the all-user usage summary
- **THEN** the system returns `403`

#### Scenario: Ordinary user requests usage history
- **WHEN** an authenticated ordinary user requests usage history with or without another user ID
- **THEN** the system returns only the current user's history

#### Scenario: Administrator requests filtered usage history
- **WHEN** an administrator requests usage history with a user ID filter
- **THEN** the system returns history for the requested user

#### Scenario: Ordinary user requests system dashboard
- **WHEN** an authenticated ordinary user requests system-wide dashboard data
- **THEN** the system returns `403`

### Requirement: Global operations are administrator-only
The system SHALL restrict internal task operations and global paper-library mutations to administrators while preserving public read-only paper discovery.

#### Scenario: Ordinary user attempts a global paper mutation
- **WHEN** an authenticated ordinary user requests ingestion, import, generated global metadata, or permanent deletion
- **THEN** the system returns `403`

#### Scenario: Ordinary user submits an internal task
- **WHEN** an authenticated ordinary user submits or inspects an internal background task
- **THEN** the system returns `403`

#### Scenario: Visitor searches the paper library
- **WHEN** a visitor searches papers or opens a paper detail page
- **THEN** the system serves the existing public read-only response

### Requirement: Frontend reflects administrator boundaries
The frontend SHALL hide prominent global paper-library mutation controls from ordinary users while retaining personal collection actions.

#### Scenario: Ordinary user opens the paper library
- **WHEN** an authenticated ordinary user views the paper library
- **THEN** the system hides ingestion, import, batch global tagging, and permanent global deletion controls

#### Scenario: Administrator opens the paper library
- **WHEN** an administrator views the paper library
- **THEN** the system displays global paper-library management controls
