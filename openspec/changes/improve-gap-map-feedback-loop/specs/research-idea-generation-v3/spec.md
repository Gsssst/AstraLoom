## MODIFIED Requirements

### Requirement: Candidate Search Tree
The system SHALL refine generated research candidates through a traceable bounded search tree that can use LLM-assisted critique-and-evolution with deterministic fallback expansion, user-selected gap constraints, and user-provided Gap Map feedback.

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

#### Scenario: Candidate generation respects gap feedback
- **WHEN** selected gaps include user edits, ratings, feedback labels, or notes
- **THEN** generated and evolved candidates use that feedback as guidance and avoid rejected or misaligned gaps when alternatives are available.

### Requirement: Persist Quality Signals
The system SHALL persist search tree, novelty check, similar-work collision details, adversarial review data, diversity-aware selection metadata, gap-selection metadata, and Gap Map feedback metadata on selected Ideas or their originating run.

#### Scenario: Selected proposal stores v3 signals
- **WHEN** a candidate is persisted as a Research Idea
- **THEN** its review metadata includes novelty check, ranked similar work, collision risk, source coverage, adversarial review, search tree, adjusted aggregate score, selection rationale, selection score, diversity facets, and gap-selection metadata.

#### Scenario: Diverse proposal selection records rationale
- **WHEN** final proposals are selected from reviewed candidates
- **THEN** the run records selected candidate titles, suppressed near-duplicates, selected gap constraints, and diversity rationale in the review summary.

#### Scenario: Gap feedback is preserved for generation audit
- **WHEN** proposal generation continues from a Gap Map with user feedback
- **THEN** the run review summary records a concise summary of the gap ratings, labels, notes, and refined gap titles used during generation.
