## ADDED Requirements

### Requirement: Selected proposals are self-checked before persistence
The research idea workbench SHALL automatically self-check selected Top Proposals before saving them as persisted research ideas.

#### Scenario: Self-check selected proposal
- **WHEN** candidate review and diversity-aware selection choose a Top Proposal
- **THEN** the backend critiques novelty risk, scope boundary, mechanism clarity, experiment minimality, and failure condition before persistence
- **AND** the candidate's compact `idea_brief` is rewritten or normalized from the critique
- **AND** legacy fields such as gap, hypothesis, approach, proposal outline, review scores, and experiment plan remain available

#### Scenario: Store self-check metadata
- **WHEN** a self-checked proposal is persisted
- **THEN** its review metadata includes `selection_self_check`
- **AND** the metadata records status, critique, rewrite summary, quality gates, and evidence references used by the check

#### Scenario: Self-check fallback
- **WHEN** the self-check model response is unavailable or invalid
- **THEN** the backend persists deterministic fallback self-check metadata
- **AND** proposal generation completes without dropping the selected proposal

#### Scenario: Display self-check compactly
- **WHEN** a user opens a self-checked proposal
- **THEN** the proposal detail indicates that the Idea Brief was automatically checked
- **AND** detailed self-check critique remains inside existing collapsed secondary details rather than appearing as a large always-visible panel
