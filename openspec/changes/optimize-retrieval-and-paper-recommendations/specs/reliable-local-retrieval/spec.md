## ADDED Requirements

### Requirement: Retrieval Ranking Uses Diversified Quality Signals
Local retrieval SHALL combine core relevance with bounded metadata quality and diversity signals before returning ranked paper results.

#### Scenario: Query has multiple lexical variants
- **WHEN** local retrieval receives an academic query
- **THEN** the retrieval layer evaluates deterministic query variants in addition to the original query
- **AND** combines their results without duplicating papers.

#### Scenario: Retrieved papers differ in metadata readiness
- **WHEN** papers have comparable relevance scores
- **THEN** papers with stronger metadata, full text, embeddings, and citation signals receive a bounded ranking boost
- **AND** the boost does not exceed the core relevance contribution.

#### Scenario: Retrieved papers are near duplicates
- **WHEN** multiple candidates have highly similar titles, tags, or identifiers
- **THEN** the final ranked list suppresses redundant candidates unless needed to fill the requested result count.

### Requirement: Evidence Chunk Retrieval Is Section And Redundancy Aware
Paper evidence retrieval SHALL prefer chunks from query-relevant sections and avoid returning redundant snippets.

#### Scenario: Query names a paper section
- **WHEN** a user query asks about a known section such as method, experiment, or related work
- **THEN** chunks from that section receive a ranking preference.

#### Scenario: Top chunks overlap heavily
- **WHEN** multiple candidate chunks contain substantially overlapping text
- **THEN** the retrieval result keeps the highest-scoring chunk and favors non-redundant alternatives.
