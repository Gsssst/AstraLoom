## MODIFIED Requirements

### Requirement: Research Idea Workbench interface
The system SHALL present the research project page as a workbench that exposes pipeline progress, Evidence Map, Gap Map, candidate pool, selected proposals, and proposal-level collision evidence.

#### Scenario: Inspect intermediate artifacts
- **WHEN** a user opens a project with a completed or running workbench run
- **THEN** the page displays the latest stage and allows the user to inspect available evidence, gaps, candidates, and proposals

#### Scenario: Distinguish score dimensions
- **WHEN** a user views a reviewed proposal
- **THEN** the interface displays review dimensions and rationale rather than only an opaque aggregate score

#### Scenario: Inspect similar work collisions
- **WHEN** a reviewed proposal has novelty collision metadata
- **THEN** the interface displays collision risk, top similar-work entries, their sources, and concise reasons without hiding the existing proposal details.

### Requirement: Persist top proposals
The system SHALL select and persist top proposals as enriched research ideas compatible with the existing idea discussion, validation, and code-generation flows.

#### Scenario: Complete a successful run
- **WHEN** candidate review finishes successfully
- **THEN** the run enters `complete`, stores its review summary, and persists the selected top proposals with evidence, review, novelty collision, and experiment-plan metadata

#### Scenario: Continue discussing a selected proposal
- **WHEN** the user opens a persisted top proposal
- **THEN** the existing discussion and code-generation actions remain available

#### Scenario: Validate related work from collision metadata
- **WHEN** the user requests validation for a selected proposal with similar-work collision metadata
- **THEN** the validation summary includes those similar works as related-work candidates before falling back to generic evidence ranking.
