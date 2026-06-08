# research-proposal-progress-board Specification

## Purpose
Expose a project-level progress board for saved Research Idea Proposals so users can quickly see which ideas need evidence, experiment design, review-guided revision, feedback-driven evolution, writing, or final decision work.

## Requirements
### Requirement: Project Proposal Progress Board Is Derived From Proposal Signals
The system SHALL provide a project-level Proposal progress board using existing Proposal, validation, execution, experiment, discussion, review package, lineage, revision, and decision data.

#### Scenario: Board requested for a project with Proposals
- **WHEN** an authenticated owner requests the progress board for a research project
- **THEN** the response groups accessible Proposals by derived status and includes each Proposal's priority score, blockers, signals, and recommended next action.

#### Scenario: Board requested for an empty project
- **WHEN** a project has no saved Proposals
- **THEN** the response includes empty groups and a summary indicating no actionable Proposals.

### Requirement: Proposal Board Status Is Actionable And Stable
The board SHALL classify Proposals into stable actionable statuses using validation, execution, review-package, feedback, and revision signals.

#### Scenario: Proposal has insufficient evidence
- **WHEN** validation reports sparse evidence coverage
- **THEN** the Proposal appears in the needs-evidence group with evidence blockers and an evidence-focused next action.

#### Scenario: Proposal has experiment feedback
- **WHEN** a Proposal has linked experiment feedback with results
- **THEN** the Proposal appears in the needs-evolution group unless it is rejected or implemented.

#### Scenario: Proposal is ready for writing
- **WHEN** validation marks writing readiness as ready, execution readiness is ready, and review package has no blocking objections
- **THEN** the Proposal appears in the ready-for-writing group with a writing-draft next action.

#### Scenario: Proposal has review blockers
- **WHEN** a Proposal review package contains blocking objections, weak writing readiness, or required experiments
- **THEN** the Proposal appears in a review-revision group with a review-guided revision next action.

#### Scenario: Proposal has revised child
- **WHEN** a Proposal has one or more child revisions
- **THEN** the board exposes revision signals so users can compare versions or continue with the latest child.

### Requirement: Frontend Shows Proposal Progress Board
The research project page SHALL include a board view that groups Proposals by progress state and exposes next-step actions.

#### Scenario: User opens board tab
- **WHEN** the user opens the Proposal progress board
- **THEN** the page displays grouped columns with counts, priority scores, blockers, signals, and recommended actions
- **AND** dynamic card content including long titles, blocker messages, signals, and actions remains inside each Proposal card without horizontal overflow.

#### Scenario: User triggers recommended action
- **WHEN** the user selects a board card's recommended action
- **THEN** the page opens or invokes the existing relevant workflow without losing the current workbench state.

#### Scenario: Board load fails
- **WHEN** the board endpoint fails
- **THEN** the page uses existing API recovery guidance and leaves the existing Proposal list usable.

#### Scenario: User acts on review revision recommendation
- **WHEN** a board item recommends review-guided revision or version comparison
- **THEN** the page opens the corresponding review package or comparison workflow for that Proposal.
