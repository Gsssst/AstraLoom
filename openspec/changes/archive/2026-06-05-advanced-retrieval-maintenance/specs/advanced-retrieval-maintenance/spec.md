## ADDED Requirements

### Requirement: Explainable Search Diagnostics

Administrators SHALL receive human-readable explanations and next steps when diagnosing a local search query.

#### Scenario: Diagnostic branch has no results

- **GIVEN** an administrator runs diagnostics for a query
- **WHEN** a retrieval branch returns no results or errors
- **THEN** the response explains likely causes using observable state
- **AND** includes recommended maintenance actions where applicable.

### Requirement: Maintenance Recommendations

Administrators SHALL be able to view prioritized repair recommendations for retrieval quality.

#### Scenario: Knowledge base has missing artifacts

- **GIVEN** papers are missing full text or embeddings
- **WHEN** the administrator opens the maintenance panel
- **THEN** the system shows grouped recommendations with severity, reason, action, and sample papers.

### Requirement: Transparent Low-Coverage Answer Status

AI chat and paper Q&A SHALL disclose low local retrieval coverage before generating answers.

#### Scenario: Local retrieval has no supporting references

- **GIVEN** local retrieval is enabled
- **WHEN** no local references are retrieved or embedding coverage is low
- **THEN** the stream status indicates the limitation and suggests knowledge-base maintenance rather than implying full coverage.
