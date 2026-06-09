## MODIFIED Requirements

### Requirement: Explainable deduplication and review
The system SHALL remove substantially overlapping candidates and SHALL review remaining candidates with an explainable multidimensional rubric.

#### Scenario: Build proposal evidence grounding matrix
- **WHEN** a candidate is reviewed with an available Evidence Map
- **THEN** the workbench computes a claim-level evidence grounding matrix for the candidate
- **AND** each matrix row records the claim, claim type, support level, support evidence references, and risk note

#### Scenario: Penalize weak evidence grounding
- **WHEN** a candidate has missing or weak support for central proposal claims
- **THEN** quality adjustment and selection ranking reduce its priority with an explainable evidence-grounding rationale

### Requirement: Persist top proposals
The system SHALL select and persist top proposals as enriched research ideas compatible with the existing idea discussion, validation, and code-generation flows while preserving selection rationale.

#### Scenario: Persist proposal evidence grounding metadata
- **WHEN** a selected proposal has evidence grounding metadata
- **THEN** the proposal review metadata records grounding score, claim support counts, weak or missing claims, and claim-to-evidence rows
- **AND** downstream validation and writing handoff can reuse that metadata without rerunning proposal generation

### Requirement: Research Idea Workbench interface
The system SHALL present the research project page as a workbench that exposes pipeline progress, Evidence Map, Gap Map, candidate pool, selected proposals, proposal-level collision evidence, selection rationale, Gap Map selection controls, and Gap Map feedback controls.

#### Scenario: Inspect proposal evidence grounding
- **WHEN** a reviewed proposal has evidence grounding metadata
- **THEN** the interface displays a compact grounding summary, weak or missing claims, and supporting evidence paper tags inside the proposal detail view
