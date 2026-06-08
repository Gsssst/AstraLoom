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

### Requirement: Manuscript And Survey Workflows Are Separated
The Writing page SHALL separate manuscript writing from survey/literature-review workflows.

#### Scenario: User opens paper writing mode
- **WHEN** the user opens paper writing mode
- **THEN** the default screen is the manuscript workbench and does not show survey draft creation as the primary action.

#### Scenario: User wants to create a survey
- **WHEN** the user chooses the survey workflow
- **THEN** the UI exposes literature-review, paper comparison, evidence table, and research-gap generation separately from manuscript section editing.

### Requirement: Template Setup Is Not The Main Manuscript Entry
The Writing page SHALL avoid making conference template selection the primary manuscript creation step.

#### Scenario: User creates a manuscript
- **WHEN** the user creates a manuscript project
- **THEN** the default path creates a chapter-based manuscript without requiring ACL/CVPR/NeurIPS template selection first.

#### Scenario: User prepares submission export
- **WHEN** the user needs official formatting
- **THEN** template/profile upload remains available from export or submission readiness rather than the main writing editor.

