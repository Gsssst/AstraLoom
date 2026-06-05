## ADDED Requirements

### Requirement: Candidate Search Tree
The system SHALL refine generated research candidates through a traceable lightweight search tree.

#### Scenario: Candidate lineage is recorded
- **WHEN** the workbench expands generated candidates
- **THEN** each expanded candidate includes tree metadata with round, operator, and lineage.

### Requirement: Novelty Check
The system SHALL evaluate candidate novelty against available evidence.

#### Scenario: Similar candidate is flagged
- **WHEN** a candidate substantially overlaps with an evidence paper title or abstract
- **THEN** the candidate receives a `too_similar` or `incremental` novelty status with nearest evidence metadata.

#### Scenario: Distinct candidate is marked likely novel
- **WHEN** a candidate has low overlap with available evidence
- **THEN** the candidate receives a `likely_novel` status and a higher novelty score.

### Requirement: Adversarial Review
The system SHALL generate adversarial review signals for each candidate before final selection.

#### Scenario: Missing baseline is objected
- **WHEN** a candidate lacks a strong baseline or clear metrics
- **THEN** the adversarial review includes objections and a non-zero penalty.

### Requirement: Persist Quality Signals
The system SHALL persist search tree, novelty check, and adversarial review data on selected Ideas.

#### Scenario: Selected proposal stores v3 signals
- **WHEN** a candidate is persisted as a Research Idea
- **THEN** its review metadata includes novelty check, adversarial review, search tree, and adjusted aggregate score.

### Requirement: Show Quality Signals In UI
The frontend SHALL show novelty and adversarial review signals in Proposal details.

#### Scenario: User opens Proposal details
- **WHEN** the user expands a Proposal
- **THEN** the page displays novelty status, adversarial verdict, top objections, and search tree source when present.
