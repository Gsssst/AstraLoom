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
