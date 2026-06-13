## ADDED Requirements

### Requirement: Reconciliation runs are singleton
The system SHALL prevent concurrent `reconcile_paper_processing` executions from processing paper batches at the same time when the shared lock backend is available.

#### Scenario: Reconciliation already running
- **WHEN** a reconciliation task starts while another reconciliation task owns the active lock
- **THEN** the later task SHALL exit without selecting or processing papers and return a skipped/locked result

#### Scenario: Reconciliation lock released
- **WHEN** a reconciliation task finishes or fails after acquiring the lock
- **THEN** the system SHALL release its lock ownership so a later scheduled run can process the next batch

### Requirement: Fresh running papers are skipped
The system SHALL skip papers whose processing metadata contains running steps that are newer than the running-step timeout.

#### Scenario: Paper already processing
- **WHEN** the reconciler inspects a paper with fresh `running_steps`
- **THEN** the paper SHALL remain visible as processing and SHALL NOT be selected for the current reconciliation batch

### Requirement: Stale running papers recover
The system SHALL treat running metadata older than the running-step timeout as stale and allow the paper to be retried.

#### Scenario: Worker crashed during paper processing
- **WHEN** the reconciler inspects a paper with `running_steps` older than the timeout
- **THEN** the system SHALL clear the stale running state and allow missing or failed artifacts to be processed again
