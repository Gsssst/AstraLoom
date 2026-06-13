## ADDED Requirements

### Requirement: Paper Detail Shows Processing Timeline
The paper library SHALL expose a per-paper processing timeline for local papers that covers PDF availability, full text, structured parsing, visual evidence/OCR, vector embeddings, and BM25/search readiness.

#### Scenario: User opens a paper detail page
- **WHEN** a local paper detail response includes processing metadata
- **THEN** the paper detail page displays each processing step with its state, short detail, and relevant timestamp when available.

#### Scenario: A processing step failed
- **WHEN** a processing step has recorded failure metadata
- **THEN** the timeline displays the failed state and the failure reason without requiring the user to open the maintenance center.

#### Scenario: A processing step is not complete
- **WHEN** a processing step is queued, running, pending, stale, or failed
- **THEN** the timeline includes an automation or retry hint explaining that the background pipeline will continue or retry the work.

#### Scenario: Paper status API is used
- **WHEN** a client requests a paper's processing status from the paper API
- **THEN** the response includes the same ordered timeline data used by the paper detail page.
