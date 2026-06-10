## ADDED Requirements

### Requirement: PDF proxy diagnostics are available for deployments
The repository SHALL provide a server-runnable diagnostic script that checks production PDF proxy URLs without requiring extra Python packages.

#### Scenario: Operator diagnoses a PDF preview failure
- **WHEN** an operator runs the diagnostic script with a PDF proxy URL
- **THEN** it reports network reachability, HTTP status, relevant headers, first-byte timing, sampled bytes, and PDF signature status
- **AND** it includes a short summary of likely failure layers.

#### Scenario: Proxy range behavior needs inspection
- **WHEN** the diagnostic script probes the PDF URL
- **THEN** it sends a bounded Range request
- **AND** reports whether the server returns partial content or treats the request as a full response.
