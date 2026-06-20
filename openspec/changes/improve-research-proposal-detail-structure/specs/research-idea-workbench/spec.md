## ADDED Requirements

### Requirement: Persist detailed proposal outlines
The workbench SHALL persist a structured outline for each selected proposal so users can inspect the research plan beyond a loose paragraph.

#### Scenario: Selected proposal stores outline metadata
- **WHEN** a candidate is persisted as a selected proposal
- **THEN** its review metadata includes a `proposal_outline`
- **AND** the outline includes problem framing, core hypothesis, mechanism, implementation steps, expected contribution, experiment design, risk boundaries, evidence rationale, and next actions
- **AND** legacy fields such as description, hypothesis, approach, and experiment plan remain populated

#### Scenario: Candidate response omits outline fields
- **WHEN** the model returns a candidate without a complete proposal outline
- **THEN** the backend normalizes deterministic fallback values from the candidate gap, hypothesis, approach, evidence, risks, and minimum experiment

### Requirement: Proposal cards display structured research plans
The research project workbench SHALL display detailed proposal outlines as readable sections when they are available.

#### Scenario: User opens a structured proposal
- **WHEN** a user expands a proposal with `proposal_outline`
- **THEN** the interface displays separate sections for problem, hypothesis, mechanism, implementation steps, experiment design, risks, evidence rationale, and next actions
- **AND** the proposal remains compatible with existing review scores, evidence panels, next-step actions, discussion, code generation, and writing handoff controls

#### Scenario: User opens an older proposal
- **WHEN** a proposal does not have `proposal_outline`
- **THEN** the interface falls back to the existing text-based detail rendering
