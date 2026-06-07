## MODIFIED Requirements

### Requirement: Novelty Check
The system SHALL evaluate candidate novelty against available evidence and ranked similar work gathered from local and configured external scholarly sources.

#### Scenario: Similar candidate is flagged
- **WHEN** a candidate substantially overlaps with an evidence paper title, abstract, or externally retrieved similar work
- **THEN** the candidate receives a `too_similar` or `incremental` novelty status with nearest evidence metadata and ranked similar-work entries.

#### Scenario: Distinct candidate is marked likely novel
- **WHEN** a candidate has low overlap with available evidence and retrieved similar work
- **THEN** the candidate receives a `likely_novel` status, a higher novelty score, and a low collision risk.

#### Scenario: External novelty search fails
- **WHEN** an external scholarly source fails while checking candidate novelty
- **THEN** the novelty check continues using local evidence and records source coverage or source errors without failing the Idea run.

### Requirement: Persist Quality Signals
The system SHALL persist search tree, novelty check, similar-work collision details, and adversarial review data on selected Ideas.

#### Scenario: Selected proposal stores v3 signals
- **WHEN** a candidate is persisted as a Research Idea
- **THEN** its review metadata includes novelty check, ranked similar work, collision risk, source coverage, adversarial review, search tree, and adjusted aggregate score.
