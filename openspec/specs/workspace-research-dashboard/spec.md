# workspace-research-dashboard Specification

## Purpose
Provide an at-a-glance research dashboard for project spaces so users can understand papers, research ideas, drafts, activity, and next actions without treating the space as only a flat resource list.

## Requirements
### Requirement: Workspace detail exposes dashboard summary

The system SHALL include dashboard metrics in workspace detail responses.

#### Scenario: Workspace has linked resources

- **GIVEN** a workspace has linked papers and writing projects
- **WHEN** a member loads workspace detail
- **THEN** the response includes dashboard progress, stage, status cards, and resource balance

### Requirement: Workspace dashboard shows research progress at a glance

The frontend SHALL show KPI cards and progress guidance on the workspace detail page.

#### Scenario: User opens workspace

- **GIVEN** workspace detail data is available
- **WHEN** the page renders
- **THEN** the dashboard shows linked resource counts, progress score, and current stage

### Requirement: Workspace dashboard preserves resource operations

The frontend SHALL preserve resource binding, unlinking, member management, and activity visibility.

#### Scenario: Editor binds resource from dashboard

- **GIVEN** the user is a workspace editor
- **WHEN** they bind a candidate resource from the dashboard
- **THEN** linked resources and activity refresh as before
