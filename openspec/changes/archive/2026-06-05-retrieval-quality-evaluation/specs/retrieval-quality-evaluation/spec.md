## ADDED Requirements

### Requirement: Retrieval quality is measured with versioned benchmark cases
The system SHALL store a version-controlled local retrieval benchmark with a query and one or more stable relevant-paper identifiers per case.

#### Scenario: Evaluator loads benchmark
- **WHEN** retrieval evaluation is requested
- **THEN** the system loads versioned benchmark cases without mutating application data

### Requirement: Evaluator reports standard ranking metrics
The system SHALL calculate `Recall@K`, `MRR`, and `nDCG@K` for each evaluated retrieval mode.

#### Scenario: Relevant paper ranks first
- **WHEN** a benchmark query returns its relevant paper at rank one
- **THEN** the query contributes full reciprocal-rank and discounted-gain credit

#### Scenario: Relevant paper is missing
- **WHEN** a benchmark query does not return any relevant paper in the top K
- **THEN** the query contributes zero recall, reciprocal-rank, and discounted-gain credit

### Requirement: Evaluation is an administrator operation
The system SHALL expose an administrator-only endpoint for on-demand local retrieval evaluation.

#### Scenario: Ordinary user requests evaluation
- **WHEN** an authenticated ordinary user requests retrieval evaluation
- **THEN** the system returns `403`

#### Scenario: Administrator evaluates BM25
- **WHEN** an administrator requests BM25 retrieval evaluation
- **THEN** the system returns benchmark metadata, aggregate metrics, and per-query rankings
