## ADDED Requirements

### Requirement: Workbench generation can be stopped
The system SHALL allow an authenticated project owner to stop a running Research Idea Workbench run and SHALL persist the stopped run as cancelled.

#### Scenario: Stop a running workbench run
- **WHEN** a project owner requests cancellation for a running idea workbench run in one of their projects
- **THEN** the run status becomes `cancelled`
- **AND** the run keeps its latest stage, progress, and artifacts
- **AND** the run message explains that generation was stopped by the user

#### Scenario: Stop is idempotent for terminal runs
- **WHEN** a project owner requests cancellation for a completed, failed, or already cancelled run
- **THEN** the system returns the persisted run without changing its terminal status

#### Scenario: Deny cancellation of another user's run
- **WHEN** an authenticated user requests cancellation for a run that belongs to another user's project
- **THEN** the system returns a not-found response without exposing run contents

### Requirement: Workbench stream cancellation is recoverable
The system SHALL stop the in-process workbench stream task when the browser cancels or disconnects and SHALL leave recoverable persisted run state.

#### Scenario: Browser aborts the stream
- **WHEN** the browser aborts an active idea workbench stream request
- **THEN** the backend cancels the stream task it started
- **AND** the latest run can be fetched with status `cancelled`

#### Scenario: Completed stream remains complete
- **WHEN** an idea workbench stream completes successfully before cancellation cleanup runs
- **THEN** the run remains `complete`
- **AND** the persisted top proposals remain available

### Requirement: Workbench generation status is actionable
The research project page SHALL present generation status with clear active-stage, stop, retry, and next-action controls.

#### Scenario: Running generation shows stop control
- **WHEN** a workbench run is actively generating
- **THEN** the page displays the active stage and progress
- **AND** the page provides a stop control for the current generation

#### Scenario: Failed generation can be retried
- **WHEN** the latest workbench run failed
- **THEN** the page displays the failure reason and last stage
- **AND** the page provides a retry action that starts a new run

#### Scenario: Cancelled generation can be restarted
- **WHEN** the latest workbench run was cancelled
- **THEN** the page displays that generation was stopped
- **AND** the page provides a restart action that starts a new run

#### Scenario: Completed generation points to proposals
- **WHEN** a workbench run completes with selected proposals
- **THEN** the page highlights that top proposals are ready
- **AND** the page provides a next action to inspect the proposals
