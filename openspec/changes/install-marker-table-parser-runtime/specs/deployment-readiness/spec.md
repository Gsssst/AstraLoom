## ADDED Requirements

### Requirement: Marker table parser runtime is available when configured
Docker deployments that configure Marker table repair SHALL install the Marker CLI runtime required by the project-owned table parser adapter.

#### Scenario: Backend image exposes Marker CLI
- **WHEN** `PDF_TABLE_PARSER_COMMAND` is configured to run `parse_tables_marker.py`
- **THEN** the backend runtime SHALL provide a `marker_single` executable through the configured parser binary path
- **AND** the adapter script SHALL be able to reach the Marker CLI boundary.

#### Scenario: Worker image receives the same parser runtime
- **WHEN** worker-side jobs use the same table repair configuration
- **THEN** the worker runtime SHALL include the same Marker CLI dependency
- **AND** table repair behavior SHALL not depend on which service processes the job.
