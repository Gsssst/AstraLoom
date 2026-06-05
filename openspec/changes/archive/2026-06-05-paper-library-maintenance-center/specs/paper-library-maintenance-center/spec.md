## ADDED Requirements

### Requirement: Paper Library Exposes Maintenance Center
The paper library SHALL provide a first-class maintenance center view for knowledge-base retrieval health.

#### Scenario: Admin opens maintenance center
- **WHEN** an administrator selects the maintenance view in the paper library
- **THEN** the page displays total papers, full-text coverage, embedding coverage, BM25 status, missing full-text samples, and missing embedding samples.

#### Scenario: Non-admin opens maintenance center
- **WHEN** a non-admin user selects the maintenance view
- **THEN** the page explains that retrieval maintenance requires administrator permission and does not expose privileged repair actions.

### Requirement: Maintenance Center Supports Repair Actions
The maintenance center SHALL surface prioritized repair actions and let administrators run bounded maintenance jobs.

#### Scenario: Recommendations are available
- **WHEN** maintenance recommendations are returned
- **THEN** the page shows severity, reason, sample papers, and the action button for each recommendation.

#### Scenario: Admin runs a repair action
- **WHEN** the admin triggers BM25 rebuild, embedding backfill, or full-text backfill
- **THEN** the page calls the corresponding maintenance endpoint and refreshes health after completion.

### Requirement: Maintenance Center Explains Retrieval Diagnostics
The maintenance center SHALL let administrators diagnose one query across BM25, dense, and hybrid retrieval branches.

#### Scenario: Query diagnostic runs
- **WHEN** the admin enters a query and runs diagnostics
- **THEN** the page displays the summary, normalized query terms, branch hits, branch explanations, and recommended actions.

### Requirement: Maintenance Center Highlights Collection Readiness
The maintenance center SHALL summarize paper collection readiness for idea generation.

#### Scenario: Collections have diagnostics
- **WHEN** collections include diagnostics
- **THEN** the page lists collections with paper count, full-text coverage, embedding coverage, readiness status, and warnings.
