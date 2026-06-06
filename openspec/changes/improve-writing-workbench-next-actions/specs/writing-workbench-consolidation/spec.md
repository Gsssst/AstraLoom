## MODIFIED Requirements

### Requirement: Writing Workbench Shows Next Actions

The frontend SHALL display project-level stage, risk, blockers, and next actions before section editing tools.

#### Scenario: Draft has weak evidence

- **WHEN** the selected project has low evidence coverage or external-only evidence
- **THEN** the workbench summary shows an evidence-related blocker
- **AND** recommends補证据/生成证据对比表 before final export.

#### Scenario: Template is not bound

- **WHEN** the selected project has no official submission template profile
- **THEN** the workbench summary clearly states that built-in structure templates do not guarantee current-year venue formatting.

#### Scenario: User opens a selected writing project

- **WHEN** a writing project is selected and a workbench summary is available
- **THEN** the project page shows the current writing stage, risk level, readiness status, and a primary next-action area before section editors.

#### Scenario: Project has workflow blockers

- **WHEN** the selected project has empty sections, short sections, missing evidence, unmatched citations, or no official template profile
- **THEN** the workbench summary presents those blockers as compact status chips.

#### Scenario: User chooses a next action

- **WHEN** a user clicks a recommended next action or quick link from the workbench summary
- **THEN** the page scrolls to the relevant sections, evidence, or export area without changing the selected project.
