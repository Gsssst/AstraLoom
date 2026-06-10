## ADDED Requirements

### Requirement: Writing project panel interactions are stable
The writing project panel SHALL keep create, select, and delete interactions from causing duplicate submissions or stale selected project renders.

#### Scenario: Project creation succeeds
- **WHEN** a user creates a writing project successfully
- **THEN** the create modal closes
- **AND** the create form resets
- **AND** the newly created project is selected once.

#### Scenario: User deletes a project card
- **WHEN** the user clicks the delete action on a project card
- **THEN** the click does not trigger project selection
- **AND** if the deleted project is selected, the writing page clears the selected project and dependent writing state.

#### Scenario: Project action fails
- **WHEN** project creation or deletion fails
- **THEN** the UI shows an error message instead of silently failing or blanking the page.
