# research-idea-iteration-timeline Specification

## Purpose
Expose a unified read-only timeline and version comparison for saved Research Idea Proposals so users can inspect how an idea moved through creation, AI discussion, validation, structured review, experiment feedback, and version evolution.

## Requirements
### Requirement: Proposal Iteration Timeline Is Derived From Existing Lifecycle Data
The system SHALL provide a read-only iteration timeline and version-comparison summary for a saved Research Idea Proposal using existing Proposal, discussion, validation, execution, experiment, review package, and lineage data.

#### Scenario: Timeline requested for accessible Proposal
- **WHEN** an authenticated owner requests the iteration timeline for a saved Proposal
- **THEN** the response includes ordered events for creation, review/validation, execution readiness, Copilot discussion milestones, linked experiments, parent evolution, review-guided revision, and child versions when those records exist.

#### Scenario: Timeline requested for sparse Proposal
- **WHEN** a Proposal has no discussions, experiments, review package, or child versions
- **THEN** the response still includes creation and current validation/execution summary events without failing.

#### Scenario: Version comparison requested
- **WHEN** an authenticated owner requests version comparison for a Proposal with a parent version
- **THEN** the response compares hypothesis, approach, experiment plan, evidence count, risk/review signals, and revision rationale between parent and child.

### Requirement: Timeline Events Are Structured And Bounded
The timeline API SHALL return structured, bounded events that are stable for frontend rendering.

#### Scenario: Discussion history is long
- **WHEN** a Proposal has many Copilot discussion entries
- **THEN** the timeline includes only bounded assistant milestones with mode, risks, next actions, suggested questions, and evolution focus rather than every raw log entry.

#### Scenario: Event ordering is requested
- **WHEN** the backend returns timeline events
- **THEN** events are sorted by timestamp and include stable type, title, summary, severity, tags, and details fields.

#### Scenario: Review package exists
- **WHEN** a Proposal has a structured review package
- **THEN** the timeline includes a bounded review event summarizing objections, required experiments, and revision focus.

### Requirement: Frontend Shows Iteration Timeline For A Proposal
The research project page SHALL let users inspect the Proposal iteration timeline and version comparison from Proposal cards and Copilot.

#### Scenario: User opens timeline
- **WHEN** the user clicks the iteration timeline action for a Proposal
- **THEN** the page opens a focused timeline view with categorized events, concise summaries, tags, and actionable details.

#### Scenario: Timeline load fails
- **WHEN** the timeline endpoint fails
- **THEN** the page uses the existing API recovery guidance and keeps the current workbench state intact.

#### Scenario: User opens version comparison
- **WHEN** the user opens comparison for a revised Proposal
- **THEN** the page displays parent-versus-child changes in core hypothesis, approach, experiment, evidence, risk signals, and revision rationale.
