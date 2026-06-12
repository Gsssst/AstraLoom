## ADDED Requirements

### Requirement: Low-Quality Table Repair Queue
The maintenance center SHALL detect low-quality table parses and provide a repair action.

#### Scenario: Low-quality tables produce recommendation
- **WHEN** papers have structured PDF metadata with low-quality table signals
- **THEN** maintenance recommendations SHALL include a table repair recommendation
- **AND** sample papers SHALL identify candidates for repair.

#### Scenario: Administrator runs table repair
- **WHEN** an administrator starts the table repair maintenance action
- **THEN** the system SHALL run a bounded repair job over low-quality table candidates
- **AND** persist repaired table metadata or actionable failure details.

#### Scenario: Parser health exposes table repair capability
- **WHEN** maintenance or paper detail status is displayed
- **THEN** parser health SHALL indicate whether the high-fidelity table parser command is configured
- **AND** SHALL keep HuggingFace mirror/cache environment settings visible for parser subprocesses.
