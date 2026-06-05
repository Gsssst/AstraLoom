## ADDED Requirements

### Requirement: Writing Project Workbench Summary

The system SHALL expose a deterministic workbench summary for each accessible writing project.

#### Scenario: User opens a writing project

- **WHEN** an authenticated user opens a writing project they can read
- **THEN** the response includes project stage, progress, evidence coverage, citation risk, template status, warnings, and recommended next actions.

### Requirement: Writing Workbench Shows Next Actions

The frontend SHALL display project-level next actions before section editing tools.

#### Scenario: Draft has weak evidence

- **WHEN** the selected project has low evidence coverage or external-only evidence
- **THEN** the workbench summary shows an evidence-related warning and suggests补证据/生成证据对比表 before final export.

#### Scenario: Template is not bound

- **WHEN** the selected project has no official submission template profile
- **THEN** the workbench summary clearly states that built-in structure templates do not guarantee current-year venue formatting.

### Requirement: Existing Writing Tools Remain Reachable

The paper writing workbench SHALL keep existing one-off writing actions reachable as supporting tools.

#### Scenario: User needs a one-off citation or polishing action

- **WHEN** the user is inside paper writing mode
- **THEN** citation recommendation, Related Work, polishing, abstract generation, literature review, and comparison tools remain available.
