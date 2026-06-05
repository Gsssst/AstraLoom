# cross-module-action-center Specification

## Purpose
Provide a balanced cross-module action surface that helps users see what to do next across papers, digests, research ideas, writing drafts, and project spaces without visiting every module separately.
## Requirements
### Requirement: Authenticated users can view cross-module actions

The system SHALL expose a read-only action center endpoint for authenticated users.

#### Scenario: User opens action center

- **GIVEN** the user is authenticated
- **WHEN** they request workflow actions
- **THEN** the response includes summary counts and grouped action items across papers, research, writing, and workspaces

### Requirement: Action center recommends module-specific next steps

The system SHALL generate next-step recommendations from existing module state.

#### Scenario: User has incomplete research workflow state

- **GIVEN** the user has unread papers, draft writing projects, active research projects, or active spaces
- **WHEN** the action center is loaded
- **THEN** relevant actions link back to the module where the work should continue

### Requirement: Frontend shows a unified workflow surface

The frontend SHALL provide an action center page reachable from the main layout.

#### Scenario: User navigates from sidebar

- **GIVEN** the user is inside the app layout
- **WHEN** they click the action center menu item
- **THEN** they see grouped action cards with priority, source, description, and entry links

### Requirement: Action center can expose executable maintenance actions

The workflow action API SHALL identify when an action can be executed directly instead of only navigating to another module.

#### Scenario: Knowledge-base maintenance is needed

- **GIVEN** a user has saved papers that are missing full text or embeddings
- **WHEN** the action center builds paper workflow actions
- **THEN** the relevant action includes an API endpoint, HTTP method, action label, and admin requirement marker
- **AND** the action still includes a path to the detailed maintenance page

### Requirement: Users can run bounded maintenance actions from the action center

The frontend SHALL execute API actions from the action center and keep users informed of the result.

#### Scenario: User runs a maintenance action

- **GIVEN** the action center displays an executable knowledge-base maintenance action
- **WHEN** the user clicks its primary action button
- **THEN** the frontend calls the action endpoint
- **AND** displays a success or error message
- **AND** refreshes the action list after completion

#### Scenario: User wants detailed controls

- **GIVEN** an executable action also has a module path
- **WHEN** the user chooses to inspect details
- **THEN** the frontend navigates to the referenced module page

