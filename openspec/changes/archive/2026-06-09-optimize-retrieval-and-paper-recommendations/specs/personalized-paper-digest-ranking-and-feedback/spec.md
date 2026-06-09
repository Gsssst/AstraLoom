## ADDED Requirements

### Requirement: Paper Recommendations Use Library Feedback And Diversity
Paper recommendation ranking SHALL combine relevance with existing library feedback, metadata readiness, freshness, citation signals, and source diversity.

#### Scenario: Recommended papers include saved or manually selected local papers
- **WHEN** a recommendation candidate has explicit user/library interaction such as manual selection, saved status, or reading activity
- **THEN** that signal contributes positively to the final recommendation score.

#### Scenario: Recommended papers differ in metadata readiness
- **WHEN** candidate papers have comparable relevance
- **THEN** candidates with stronger metadata, abstracts, identifiers, embeddings, and full text are ranked higher.

#### Scenario: Recommendation candidates are concentrated in one source or topic
- **WHEN** multiple high-scoring candidates are near duplicates or from one source cluster
- **THEN** the selector preserves the strongest candidate and admits diverse alternatives when available.

#### Scenario: Recommendation ranking has insufficient LLM support
- **WHEN** LLM reranking fails or is skipped
- **THEN** the selector still returns a deterministic, diversity-aware ranking using local scoring signals.
