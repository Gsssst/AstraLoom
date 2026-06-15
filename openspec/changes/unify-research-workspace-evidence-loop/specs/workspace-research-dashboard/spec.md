## MODIFIED Requirements

### Requirement: Workspace dashboard shows research progress at a glance

The frontend SHALL show KPI cards, progress guidance, and a workflow-oriented research cockpit on the workspace detail page.

#### Scenario: User opens workspace cockpit

- **GIVEN** workspace detail data is available
- **WHEN** the page renders the overview tab
- **THEN** the dashboard shows linked resource counts, progress score, and current stage
- **AND** the cockpit summarizes paper evidence, research ideas, writing drafts, and open issues as separate workflow tracks
- **AND** each track exposes a next action appropriate to the user's workspace role

### Requirement: Workspace dashboard preserves resource operations

The frontend SHALL preserve resource binding, unlinking, member management, activity visibility, and issue visibility while adding cockpit actions.

#### Scenario: Editor uses cockpit action

- **GIVEN** the user is a workspace editor
- **WHEN** they click the cockpit paper evidence action
- **THEN** the existing resource binder is opened for papers
- **AND** the existing resource binding flow is used
