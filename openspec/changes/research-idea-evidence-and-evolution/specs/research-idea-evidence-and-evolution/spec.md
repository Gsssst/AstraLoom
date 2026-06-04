## ADDED Requirements

### Requirement: Optional external scholarly evidence
The system SHALL allow a project owner to enable external scholarly search for a Research Idea Workbench run and SHALL merge normalized external evidence into the Evidence Map with explicit provenance.

#### Scenario: Enable external search
- **WHEN** a user starts an Idea run with external scholarly search enabled
- **THEN** the system queries configured scholarly sources and stores normalized external evidence with a stable identifier, source label, source URL, and abstract excerpt

#### Scenario: External search fails
- **WHEN** one or more external scholarly sources are unavailable
- **THEN** the workbench completes with local-library evidence and records source errors without failing the entire run

### Requirement: Proposal decision states
The system SHALL allow a project owner to mark an accessible proposal as pinned, rejected, or draft without deleting proposal history.

#### Scenario: Pin a promising proposal
- **WHEN** the owner marks a draft proposal as pinned
- **THEN** the proposal status becomes `pinned` and remains available in the workbench

#### Scenario: Reject and restore a proposal
- **WHEN** the owner marks a proposal as rejected and later restores it
- **THEN** the proposal history remains intact and its status returns to `draft`

### Requirement: Structured proposal comparison
The system SHALL allow a project owner to compare two to four accessible proposals through normalized proposal data.

#### Scenario: Compare selected proposals
- **WHEN** the owner submits two to four proposal identifiers from their project
- **THEN** the system returns hypotheses, statuses, review dimensions, evidence counts, experiment plans, and lineage for side-by-side comparison

#### Scenario: Reject inaccessible comparison
- **WHEN** the comparison request contains a proposal outside the current user's projects
- **THEN** the system returns a not-found response without exposing foreign proposal data

### Requirement: Traceable single-step proposal evolution
The system SHALL allow a project owner to evolve a draft or pinned proposal into a new persisted child proposal while preserving the parent.

#### Scenario: Evolve a pinned proposal
- **WHEN** the owner requests evolution with an optional focus
- **THEN** the system creates a draft child proposal containing a refined hypothesis, review metadata, experiment plan, parent identifier, and evolution rationale

#### Scenario: Preserve the parent
- **WHEN** proposal evolution succeeds
- **THEN** the original proposal remains unchanged and both versions remain inspectable

### Requirement: Evidence and evolution interface
The system SHALL expose external evidence controls and proposal decision, comparison, and evolution actions in the Research Idea Workbench.

#### Scenario: Distinguish external evidence
- **WHEN** external evidence appears in the Evidence Map
- **THEN** the interface displays its scholarly source and provides its source link

#### Scenario: Compare from the proposal list
- **WHEN** the user selects two to four proposals and opens comparison
- **THEN** the interface presents their key trade-offs in a side-by-side view
