# writing-workbench-redesign Specification

## Purpose
Restructure the writing assistant into a project-first workbench that separates paper manuscript writing from grant/proposal writing, while making template and submission-format boundaries explicit.

## Requirements
### Requirement: Writing assistant separates paper and grant workflows

The frontend SHALL present paper manuscript writing and grant/proposal writing as distinct top-level modes.

#### Scenario: User opens writing assistant

- **GIVEN** the user navigates to the writing assistant
- **WHEN** the page renders
- **THEN** the user can choose between paper writing and grant/proposal writing without scanning unrelated feature tabs

### Requirement: Paper writing is project-first

The frontend SHALL make manuscript project management the primary paper-writing surface.

#### Scenario: User wants to continue a manuscript

- **GIVEN** the user has writing projects
- **WHEN** they open paper writing mode
- **THEN** project selection, project creation, section editing, evidence cards, citation checks, and export readiness are visible as one workbench

### Requirement: Submission formatting is template-aware

The system SHALL distinguish structure templates from official submission templates.

#### Scenario: User chooses a conference target

- **GIVEN** conference formats can change by year
- **WHEN** the user selects a target venue/profile
- **THEN** the UI explains that built-in templates are writing structure guides and official formatting requires imported or verified venue template files

### Requirement: Existing writing capabilities remain reachable

The frontend SHALL keep current writing capabilities reachable after the layout redesign.

#### Scenario: User needs a one-off writing action

- **GIVEN** the user is in paper writing mode
- **WHEN** they need citation recommendation, Related Work, polishing, abstract generation, literature review, or paper comparison
- **THEN** those actions remain available as contextual tools rather than disappearing
