# research-idea-validation-loop Specification

## Purpose
TBD - created by archiving change research-idea-validation-loop. Update Purpose after archive.
## Requirements
### Requirement: Research Ideas Can Be Validated Before Progression
The system SHALL provide a validation summary for a generated research idea before the user progresses it into experiments or writing.

#### Scenario: Validate a saved idea
- **WHEN** an authenticated user requests validation for an idea they own
- **THEN** the response includes collision risk, related work, feasibility risks, experiment checklist, writing readiness, and coverage information.

#### Scenario: Reject unauthorized validation access
- **WHEN** a user requests validation for an idea outside their workspace or ownership boundary
- **THEN** the request is rejected by the existing research authorization rules.

### Requirement: Validation Explains Evidence And Collision Risk
The validation summary SHALL explain whether an idea appears novel, incremental, or too similar to existing evidence.

#### Scenario: Idea is close to existing work
- **WHEN** the stored novelty check marks an idea as `too_similar` or `incremental`
- **THEN** validation reports elevated collision risk and lists the nearest evidence or related work that caused the warning.

#### Scenario: Evidence is sparse
- **WHEN** an idea has too few evidence items or referenced papers
- **THEN** validation reports an evidence coverage warning instead of claiming the idea is ready.

### Requirement: Validation Provides Minimum Experiment Checklist
The validation summary SHALL provide a minimum experiment checklist derived from the idea's experiment plan and review concerns.

#### Scenario: Experiment plan is incomplete
- **WHEN** datasets, baselines, metrics, implementation steps, or ablations are missing
- **THEN** validation marks the missing items and recommends concrete next actions.

#### Scenario: Experiment plan is complete enough
- **WHEN** the idea has datasets, baselines, metrics, implementation steps, and at least one evidence source
- **THEN** validation marks those checklist groups as present and can report writing readiness as ready if no blocking collision risk exists.

### Requirement: Frontend Shows Validation Loop Transparently
The research project page SHALL let users run and inspect validation for each idea.

#### Scenario: User runs validation from an idea card
- **WHEN** the user clicks the validation action on an idea card
- **THEN** the page fetches validation and displays writing readiness, collision risk, related work, risks, checklist items, and next actions in that card.

#### Scenario: Validation warns against writing
- **WHEN** validation reports evidence gaps, incomplete experiments, or high collision risk
- **THEN** the frontend clearly shows that the idea is not ready for writing and explains why.

