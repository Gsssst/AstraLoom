# research-idea-iteration-timeline Specification

## Purpose
Expose a unified read-only timeline for saved Research Idea Proposals so users can inspect how an idea moved through creation, AI discussion, validation, experiment feedback, and version evolution.

## Requirements
### Requirement: Proposal Iteration Timeline Is Derived From Existing Lifecycle Data
The system SHALL provide a read-only iteration timeline for a saved Research Idea Proposal using existing Proposal, discussion, validation, execution, experiment, and lineage data.

#### Scenario: Timeline requested for accessible Proposal
- **WHEN** an authenticated owner requests the iteration timeline for a saved Proposal
- **THEN** the response includes ordered events for creation, review/validation, execution readiness, Copilot discussion milestones, linked experiments, parent evolution, and child versions when those records exist.

#### Scenario: Timeline requested for sparse Proposal
- **WHEN** a Proposal has no discussions, experiments, or child versions
- **THEN** the response still includes creation and current validation/execution summary events without failing.

### Requirement: Timeline Events Are Structured And Bounded
The timeline API SHALL return structured, bounded events that are stable for frontend rendering.

#### Scenario: Discussion history is long
- **WHEN** a Proposal has many Copilot discussion entries
- **THEN** the timeline includes only bounded assistant milestones with mode, risks, next actions, suggested questions, and evolution focus rather than every raw log entry.

#### Scenario: Event ordering is requested
- **WHEN** the backend returns timeline events
- **THEN** events are sorted by timestamp and include stable type, title, summary, severity, tags, and details fields.

### Requirement: Frontend Shows Iteration Timeline For A Proposal
The research project page SHALL let users inspect the Proposal iteration timeline from Proposal cards and Copilot.

#### Scenario: User opens timeline
- **WHEN** the user clicks the iteration timeline action for a Proposal
- **THEN** the page opens a focused timeline view with categorized events, concise summaries, tags, and actionable details.

#### Scenario: Timeline load fails
- **WHEN** the timeline endpoint fails
- **THEN** the page uses the existing API recovery guidance and keeps the current workbench state intact.
