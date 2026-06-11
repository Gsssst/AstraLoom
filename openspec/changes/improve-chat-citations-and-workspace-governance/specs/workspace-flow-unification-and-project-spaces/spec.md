## MODIFIED Requirements

### Requirement: Users can manage project spaces
Authenticated users SHALL be able to create and manage project spaces that group research workflow resources.

#### Scenario: Create a project space
- **GIVEN** an authenticated user
- **WHEN** they create a project space with a name and optional description
- **THEN** they become the owner and initial member

#### Scenario: List accessible project spaces
- **WHEN** they request project spaces
- **THEN** the system returns spaces where they are a member

#### Scenario: Add member from selectable users
- **GIVEN** a project space owner
- **WHEN** they search for users from the add-member dialog
- **THEN** the system returns active user candidates with display name, username, email, and current membership status
- **AND** the owner can select a candidate to add or update that member's role

#### Scenario: Add member by typed account
- **GIVEN** a project space owner
- **WHEN** they type a username or email manually
- **THEN** the existing account-based member add flow remains supported
