# workflow-step-guide Specification

## Purpose
TBD - created by archiving change workflow-step-guide-unification. Update Purpose after archive.
## Requirements
### Requirement: Core workflow pages show contextual next-step guidance
The frontend SHALL show a consistent contextual workflow guide on core research workflow pages.

#### Scenario: User opens the paper library
- **WHEN** the user opens the paper library page
- **THEN** the page shows a paper-library next-step guide with actions for maintenance, paper organization, and research direction handoff

#### Scenario: User opens the research direction page
- **WHEN** the user opens the research direction page
- **THEN** the page shows a research next-step guide with actions for paper seed preparation, direction creation, and writing handoff

#### Scenario: User opens the writing page
- **WHEN** the user opens the writing page
- **THEN** the page shows a writing next-step guide with actions for project setup, evidence/citation work, and export readiness

### Requirement: Workflow guide actions route or execute predictably
Workflow guide actions SHALL either navigate to a known route or execute a local page action.

#### Scenario: Step navigates to another module
- **WHEN** the user clicks a guide step with a route target
- **THEN** the frontend navigates to that target without requiring additional configuration

#### Scenario: Step executes a local page action
- **WHEN** the user clicks a guide step with a local action target
- **THEN** the page executes the action and keeps the user in the current workflow context

### Requirement: Workflow guide explains action intent
Each workflow guide step SHALL describe why the step matters before the user clicks it.

#### Scenario: User reads a workflow step
- **WHEN** a workflow step is displayed
- **THEN** it includes a short title, status label, description, and action label

