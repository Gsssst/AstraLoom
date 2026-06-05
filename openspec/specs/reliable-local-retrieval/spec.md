# reliable-local-retrieval Specification

## Purpose
TBD - created by archiving change retrieval-quality-evaluation. Update Purpose after archive.
## Requirements
### Requirement: Retrieval modes execute their documented paths
The system SHALL provide `bm25`, `dense`, and `hybrid` local retrieval modes with distinct execution behavior.

#### Scenario: BM25 mode avoids embeddings
- **WHEN** local paper search uses `search_mode=bm25`
- **THEN** the system ranks papers with the lexical index without invoking dense embedding generation

#### Scenario: Dense mode uses vector retrieval
- **WHEN** local paper search uses `search_mode=dense`
- **THEN** the system ranks embedded papers using pgvector cosine similarity

#### Scenario: Hybrid mode fuses two ranked lists
- **WHEN** local paper search uses `search_mode=hybrid`
- **THEN** the system fuses lexical and dense ranked lists using weighted reciprocal rank fusion

#### Scenario: Embedding coverage is incomplete
- **WHEN** hybrid search runs while embedding coverage is below the configured fusion threshold
- **THEN** the system temporarily returns lexical results so a partial semantic subset cannot distort ranking

#### Scenario: Dense retrieval is unavailable
- **WHEN** dense retrieval fails during hybrid search
- **THEN** the system logs the degraded path and returns lexical results

### Requirement: Lexical retrieval prioritizes academic terms
The system SHALL tokenize normalized academic terms and SHALL assign more BM25 weight to title matches than abstract-only matches.

#### Scenario: Query contains punctuation
- **WHEN** a query contains terms such as `top-p`, `BERT`, or `attention-based`
- **THEN** the lexical tokenizer produces normalized searchable terms

#### Scenario: Term appears in a title
- **WHEN** a paper title and another paper abstract contain the same query term
- **THEN** title weighting contributes additional lexical relevance to the title match

### Requirement: BM25 cache stays current
The system SHALL refresh the in-process BM25 index when the paper library changes.

#### Scenario: New paper is ingested
- **WHEN** paper ingestion or import commits a new paper
- **THEN** the system invalidates the lexical index for the next search

#### Scenario: Cached index fingerprint changes
- **WHEN** paper count or latest paper update time differs from the cached fingerprint
- **THEN** the system rebuilds the lexical index before searching

### Requirement: Ranked local search honors filters and pagination
The system SHALL apply category and year filters to ranked local search and SHALL retrieve enough candidates for requested pages within a bounded window.

#### Scenario: User opens a later ranked page
- **WHEN** the user requests page two of a keyword search
- **THEN** the system returns the second page from a candidate window large enough to include it

#### Scenario: User filters ranked results
- **WHEN** the user applies category or year filters with a keyword query
- **THEN** the system returns only ranked papers satisfying those filters

### Requirement: Remote source modes execute correctly
The system SHALL call the selected remote paper provider for arXiv and Semantic Scholar preview searches.

#### Scenario: Semantic Scholar preview search
- **WHEN** `source=semantic_scholar` and a query is provided
- **THEN** the system requests and returns Semantic Scholar preview results

#### Scenario: Combined preview search
- **WHEN** `source=all` and a query is provided
- **THEN** the system includes local ranked results and arXiv preview results

