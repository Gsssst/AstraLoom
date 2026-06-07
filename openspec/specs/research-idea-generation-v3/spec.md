# research-idea-generation-v3 Specification

## Purpose
TBD - created by archiving change research-idea-generation-v3. Update Purpose after archive.
## Requirements
### Requirement: Candidate Search Tree
The system SHALL refine generated research candidates through a traceable bounded search tree that can use LLM-assisted critique-and-evolution with deterministic fallback expansion and user-selected gap constraints.

#### Scenario: Candidate lineage is recorded
- **WHEN** the workbench expands generated candidates
- **THEN** each expanded candidate includes tree metadata with round, operator, parent title, and lineage.

#### Scenario: Candidate is evolved from critique
- **WHEN** the LLM evolution step returns valid evolved candidates
- **THEN** the workbench includes candidates with critique, improvement, selection angle, and their parent lineage.

#### Scenario: Evolution output is unavailable
- **WHEN** the LLM evolution step fails or returns insufficient valid candidates
- **THEN** the workbench uses deterministic fallback operators to keep the search tree populated and traceable.

#### Scenario: Candidate generation respects gap constraints
- **WHEN** the run includes selected gaps and generation constraints
- **THEN** generated and evolved candidates are prompted and selected using those gaps, focus notes, research mode, risk appetite, and resource budget.

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

### Requirement: Adversarial Review
The system SHALL generate adversarial review signals for each candidate before final selection.

#### Scenario: Missing baseline is objected
- **WHEN** a candidate lacks a strong baseline or clear metrics
- **THEN** the adversarial review includes objections and a non-zero penalty.

### Requirement: Persist Quality Signals
The system SHALL persist search tree, novelty check, similar-work collision details, adversarial review data, diversity-aware selection metadata, and gap-selection metadata on selected Ideas.

#### Scenario: Selected proposal stores v3 signals
- **WHEN** a candidate is persisted as a Research Idea
- **THEN** its review metadata includes novelty check, ranked similar work, collision risk, source coverage, adversarial review, search tree, adjusted aggregate score, selection rationale, selection score, diversity facets, and gap-selection metadata.

#### Scenario: Diverse proposal selection records rationale
- **WHEN** final proposals are selected from reviewed candidates
- **THEN** the run records selected candidate titles, suppressed near-duplicates, selected gap constraints, and diversity rationale in the review summary.

### Requirement: Show Quality Signals In UI
The frontend SHALL show novelty and adversarial review signals in Proposal details.

#### Scenario: User opens Proposal details
- **WHEN** the user expands a Proposal
- **THEN** the page displays novelty status, adversarial verdict, top objections, and search tree source when present.
