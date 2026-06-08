## ADDED Requirements

### Requirement: Proposal cards expose next-step actions
The research project workbench SHALL show an actionable next-step panel for each persisted proposal using existing proposal evidence, review, experiment, validation, code, discussion, and writing state.

#### Scenario: User opens a proposal card
- **WHEN** a user expands a proposal in the research project workbench
- **THEN** the proposal details include a next-step action panel with concise action labels and rationale
- **AND** the panel includes actions that route into existing proposal workflows without leaving the project context

#### Scenario: Proposal has incomplete follow-up work
- **WHEN** a proposal lacks validation, experiment feedback, generated code, writing handoff, or sufficient evidence
- **THEN** the next-step panel surfaces those missing follow-up actions as available buttons
