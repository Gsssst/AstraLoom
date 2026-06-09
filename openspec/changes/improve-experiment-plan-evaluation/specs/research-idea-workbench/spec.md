## MODIFIED Requirements

### Requirement: Explainable deduplication and review
The system SHALL remove substantially overlapping candidates and SHALL review remaining candidates with an explainable multidimensional rubric.

#### Scenario: Build experiment quality profile
- **WHEN** a candidate has a minimum experiment plan
- **THEN** the workbench computes an experiment quality profile covering dataset clarity, baseline strength, metric alignment, ablation design, statistical validity, falsification, and compute feasibility
- **AND** the profile records blocking issues and recommended fixes

#### Scenario: Penalize weak experiment plans
- **WHEN** a candidate lacks strong baselines, ablations, statistical validity, or feasible compute assumptions
- **THEN** quality adjustment and selection ranking reduce its priority with an explainable experiment-quality rationale

### Requirement: Persist top proposals
The system SHALL select and persist top proposals as enriched research ideas compatible with the existing idea discussion, validation, and code-generation flows while preserving selection rationale.

#### Scenario: Persist experiment quality metadata
- **WHEN** a selected proposal has an experiment quality profile
- **THEN** the proposal review metadata records quality score, readiness, blocking issues, recommended fixes, and quality sub-scores
- **AND** downstream validation and experiment execution packs can reuse that metadata without recomputing proposal ranking

### Requirement: Research Idea Workbench interface
The system SHALL present the research project page as a workbench that exposes pipeline progress, Evidence Map, Gap Map, candidate pool, selected proposals, proposal-level collision evidence, selection rationale, Gap Map selection controls, and Gap Map feedback controls.

#### Scenario: Inspect experiment quality
- **WHEN** a reviewed proposal has experiment quality metadata
- **THEN** the interface displays readiness, quality score, blocking issues, and recommended fixes inside the existing proposal detail view
