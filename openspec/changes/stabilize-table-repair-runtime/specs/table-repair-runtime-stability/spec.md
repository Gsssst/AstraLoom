## ADDED Requirements

### Requirement: Table repair uses guarded parser execution
The system SHALL execute external high-fidelity table parsers with bounded runtime, bounded diagnostics, and subprocess cleanup.

#### Scenario: Parser times out
- **WHEN** a table parser exceeds the configured timeout
- **THEN** the system terminates the parser process group
- **AND** records a timeout-specific repair failure reason.

#### Scenario: Parser is killed by the operating system
- **WHEN** a table parser exits with an OOM-compatible status such as `137` or SIGKILL
- **THEN** the system records a resource-specific repair failure reason
- **AND** the maintenance result explains that the high-fidelity parser could not run in the current environment.

### Requirement: Table repair preserves actionable diagnostics
The system SHALL preserve enough parser diagnostic detail for administrators to understand repair failures without exposing unbounded stderr in user-facing payloads.

#### Scenario: Parser emits a long traceback
- **WHEN** a table parser fails with stderr longer than the public maintenance payload limit
- **THEN** the user-facing failure reason remains concise
- **AND** backend metadata or logs retain a longer diagnostic excerpt for support.

### Requirement: Marker remains optional high-fidelity repair
The system SHALL treat Marker table repair as an optional high-fidelity parser rather than a required local maintenance dependency.

#### Scenario: Marker is unsafe or unavailable
- **WHEN** Marker is not installed, is disabled, or fails a runtime guard
- **THEN** table repair attempts a lightweight fallback when available
- **AND** reports skipped high-fidelity repair without crashing the maintenance job.
