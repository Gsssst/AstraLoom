## MODIFIED Requirements

### Requirement: Asynchronous Visual Evidence Processing
The system SHALL run visual evidence extraction and crop-level OCR as background work that does not block the paper library or chat answer generation path.

#### Scenario: Evidence is missing during Q&A
- **WHEN** a user asks a question before visual evidence processing is ready
- **THEN** the system may enqueue or recommend visual evidence extraction but answers only from currently ready evidence.

#### Scenario: Extraction job completes
- **WHEN** a visual evidence job finishes successfully
- **THEN** the system persists ready evidence metadata, including OCR-enhanced visual table markdown when available, and makes it available to later Q&A turns without rerunning extraction.

#### Scenario: Single-paper extraction is long-running
- **WHEN** a user starts visual evidence extraction for one paper and OCR may require multiple model calls
- **THEN** the API returns quickly with queued/running job metadata
- **AND** the OCR work continues outside the HTTP request until it succeeds, fails, or records a recoverable error.
