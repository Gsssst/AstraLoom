# workspace-flow-unification-and-project-spaces Specification

## Purpose
Define the unified project-space workflow that groups papers, research directions, writing drafts, members, and next actions around one research effort.
## Requirements
### Requirement: Users can manage project spaces

Authenticated users SHALL be able to create and manage project spaces that group research workflow resources.

#### Scenario: Create a project space

- **GIVEN** an authenticated user
- **WHEN** they create a project space with a name and optional description
- **THEN** the space is created with the user as owner
- **AND** the owner is included in the member list

#### Scenario: List accessible project spaces

- **GIVEN** an authenticated user
- **WHEN** they request project spaces
- **THEN** the response includes spaces they own or belong to
- **AND** each space includes the user's role

### Requirement: Project spaces expose workflow summaries

Project spaces SHALL summarize paper, research, and writing workflow resources.

#### Scenario: Space has no explicit linked resources

- **GIVEN** a project space owned by a user
- **WHEN** the user opens the space
- **THEN** the response includes recent personal papers, research projects, and writing projects as starter resources
- **AND** next action suggestions are provided

#### Scenario: Space has explicit resource links

- **GIVEN** a project space has metadata resource links
- **WHEN** the user opens the space
- **THEN** linked resources are surfaced before recent fallback resources

### Requirement: Owners can manage members

Project space owners SHALL be able to add and remove members.

#### Scenario: Add member by username or email

- **GIVEN** a project space owner
- **WHEN** they add a member with username or email and a role
- **THEN** the member is added to the space
- **AND** the member can see the space in their list

#### Scenario: Non-owner attempts member management

- **GIVEN** a project space member who is not the owner
- **WHEN** they try to add or remove members
- **THEN** the request is rejected

### Requirement: Frontend provides unified workspace navigation

The frontend SHALL expose project spaces as a first-class workflow entry.

#### Scenario: User opens project spaces

- **GIVEN** an authenticated user
- **WHEN** they open the sidebar
- **THEN** they can navigate to `项目空间`
- **AND** they can create a project space or open an existing one

#### Scenario: User opens a project space

- **GIVEN** a project space exists
- **WHEN** the user opens its detail page
- **THEN** they see workflow summary cards, recent resources, members, and next-action shortcuts
