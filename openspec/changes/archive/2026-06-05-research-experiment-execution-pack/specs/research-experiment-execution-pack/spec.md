# research-experiment-execution-pack Specification

## ADDED Requirements

### Requirement: Experiment execution pack

The system SHALL provide an experiment execution pack for an owned Research Idea.

#### Scenario: Pack is requested for an Idea

- **WHEN** an authenticated owner requests an execution pack for a Research Idea
- **THEN** the response includes readiness, minimum experiment tasks, success metrics, risks, feedback status, and next actions
- **AND** the pack derives its content from the Idea's experiment plan, validation data, review data, evidence, and linked experiments.

#### Scenario: Missing setup is transparent

- **WHEN** the Idea lacks dataset, baselines, metrics, or experiment steps
- **THEN** the execution pack marks the missing setup items
- **AND** recommends concrete setup actions before writing or feedback-driven evolution.

#### Scenario: Feedback can drive iteration

- **WHEN** linked experiment feedback exists for the Idea
- **THEN** the execution pack exposes the latest feedback summary
- **AND** recommends feedback-driven Proposal evolution when structured results are present.

### Requirement: Execution pack interface

The Research Project page SHALL expose the experiment execution pack inside each Proposal detail.

#### Scenario: User opens a Proposal

- **WHEN** a user opens a Proposal card
- **THEN** they can load and inspect the experiment execution pack
- **AND** the panel shows readiness, task checklist, success metrics, risks, feedback, and next actions.
