## MODIFIED Requirements

### Requirement: Project-owned staged idea run
The system SHALL allow an authenticated project owner to start a persisted Research Idea Workbench run and SHALL track its stage, progress, configuration, intermediate artifacts, completion status, and error details.

#### Scenario: Start a workbench run
- **WHEN** an authenticated owner starts a run for one of their research projects
- **THEN** the system creates a persisted run in the `briefing` stage and begins the staged pipeline

#### Scenario: Deny access to another user's run
- **WHEN** an authenticated user requests a run that belongs to another user's project
- **THEN** the system returns a not-found response without exposing run contents

#### Scenario: User starts an idea run with selected toolbox entries
- **WHEN** a user starts an idea generation run with selected toolbox tool IDs and a tool mode
- **THEN** the run config persists the selected tool context
- **AND** candidate generation receives the selected tool names, summaries, use cases, limitations, and linked evidence

#### Scenario: User requires toolbox usage
- **WHEN** the selected tool mode is `required`
- **THEN** generated candidates are prompted to use at least one selected toolbox entry
- **AND** selected proposals record which toolbox entries influenced the candidate when available

#### Scenario: Workbench builds a toolbox fit plan
- **WHEN** a workbench run has selected toolbox entries and a Gap Map
- **THEN** the generation context includes a ranked `tool_fit_plan`
- **AND** each plan item records role, fit score, matched gaps, recommended use, risk note, and rationale

#### Scenario: Toolbox fit plan guides candidate generation
- **WHEN** candidate generation runs with a `tool_fit_plan`
- **THEN** candidate and evolution prompts receive the fit plan
- **AND** fallback candidates use the top-ranked fit item when the model response is unavailable or invalid

### Requirement: Persist top proposals
The system SHALL select and persist top proposals as enriched research ideas compatible with the existing idea discussion, validation, and code-generation flows while preserving selection rationale.

#### Scenario: Complete a successful run
- **WHEN** candidate review finishes successfully
- **THEN** the run enters `complete`, stores its review summary, and persists the selected top proposals with evidence, review, novelty collision, selection rationale, and experiment-plan metadata

#### Scenario: Continue discussing a selected proposal
- **WHEN** the user opens a persisted top proposal
- **THEN** the existing discussion and code-generation actions remain available

#### Scenario: Validate related work from collision metadata
- **WHEN** the user requests validation for a selected proposal with similar-work collision metadata
- **THEN** the validation summary includes those similar works as related-work candidates before falling back to generic evidence ranking.

#### Scenario: Persist proposal toolbox fit rationale
- **WHEN** a selected proposal is influenced by toolbox entries
- **THEN** the proposal review metadata records the relevant tool IDs, tool names, tool-fit plan, and concise tool-fit rationale
- **AND** the research project UI can display that rationale without requiring another generation run
