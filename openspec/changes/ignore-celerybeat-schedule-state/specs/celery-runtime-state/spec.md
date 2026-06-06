## ADDED Requirements

### Requirement: Celery Beat state is not source controlled
The system SHALL treat Celery Beat schedule state files as generated runtime data and exclude them from Git tracking.

#### Scenario: Scheduler state changes during development
- **WHEN** Celery Beat writes or updates a schedule state file
- **THEN** the generated state file SHALL NOT appear as a tracked source modification

### Requirement: Celery Beat state is written outside the source tree
The system SHALL configure compose-managed Celery Beat services to write schedule state outside source-controlled application directories.

#### Scenario: Development scheduler starts
- **WHEN** the development `celery-beat` service starts
- **THEN** it SHALL use a schedule state path outside the bind-mounted source tree

#### Scenario: Production scheduler starts
- **WHEN** the production override `celery-beat` service starts
- **THEN** it SHALL use a schedule state path outside the application source tree
