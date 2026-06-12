## ADDED Requirements

### Requirement: Marker Table Parser Adapter
The project SHALL provide a concrete Marker table parser adapter command for high-fidelity table repair deployments.

#### Scenario: Adapter emits repair contract
- **WHEN** the Marker adapter successfully parses a PDF
- **THEN** it SHALL print JSON with a top-level `tables` array
- **AND** each table SHALL include rows or cells usable by the high-fidelity repair pipeline.

#### Scenario: Marker unavailable
- **WHEN** Marker is not installed or `marker_single` is unavailable
- **THEN** the adapter SHALL exit with a non-zero status
- **AND** print an actionable error message to stderr.

#### Scenario: Docker forwards table parser config
- **WHEN** Docker Compose starts backend or worker services
- **THEN** `PDF_TABLE_PARSER_COMMAND`, timeout, and max output settings SHALL be available in those containers.
