## MODIFIED Requirements

### Requirement: Idea Copilot Uses Rich Research Context
The system SHALL answer Research Idea Copilot discussion requests and structured review-package requests using bounded context from the selected Proposal, available evidence, validation summary, execution pack, lineage, evolution metadata, reviewer-style review package, and recent discussion history.

#### Scenario: Copilot discusses an evidence-backed Proposal
- **WHEN** an authenticated project owner asks the Copilot about a saved Proposal
- **THEN** the backend includes the Proposal's core fields, evidence/review metadata, validation summary, execution readiness, lineage summary, reviewer-style review package when present, and recent discussion turns in the model context.

#### Scenario: Copilot handles sparse context
- **WHEN** a Proposal lacks evidence, validation, execution, lineage, or review-package data
- **THEN** the backend still answers and marks the missing context in a context summary instead of failing the discussion request.

### Requirement: Idea Copilot Supports Iteration Modes
The system SHALL allow the user to choose a Copilot mode for each discussion turn.

#### Scenario: User selects skeptic mode
- **WHEN** the user sends a Copilot message in skeptic mode
- **THEN** the backend prompts the model to critique novelty, feasibility, evidence gaps, and experiment risk instead of giving only supportive refinement advice.

#### Scenario: Invalid mode is submitted
- **WHEN** the request includes an unsupported Copilot mode
- **THEN** request validation rejects the payload with a clear validation error.

### Requirement: Idea Copilot Returns Actionable Structured Metadata
The system SHALL return structured Copilot metadata alongside the assistant reply and SHALL persist reviewer-style review package metadata when requested.

#### Scenario: Copilot reply succeeds
- **WHEN** the model returns a Copilot answer
- **THEN** the API response includes the reply, selected mode, full discussion log, context summary, risks, next actions, suggested questions, and an evolution focus when available.

#### Scenario: Model returns unstructured text
- **WHEN** the model does not return valid structured JSON
- **THEN** the backend preserves the visible reply and returns deterministic fallback metadata derived from validation and execution context.

#### Scenario: Review package requested
- **WHEN** the owner requests a structured review package for a Proposal
- **THEN** the backend persists reviewer-style summary, contributions, weakest assumptions, objections, required experiments, revision plan, writing readiness, and next revision focus.

### Requirement: Discussion Can Create A Traceable Proposal Evolution
The system SHALL let the user convert Copilot discussion output or structured review guidance into a new Proposal version.

#### Scenario: Evolve from discussion focus
- **WHEN** the owner requests discussion-driven evolution for a draft or pinned Proposal
- **THEN** the backend creates a traceable child Proposal using the supplied focus or latest Copilot evolution focus and preserves the parent Proposal.

#### Scenario: Evolve rejected Proposal from discussion
- **WHEN** the owner requests discussion-driven evolution for a rejected Proposal
- **THEN** the backend rejects the request using the same eligibility rules as the existing Proposal evolution flow.

#### Scenario: Revise from review package
- **WHEN** the owner requests review-guided revision for a draft or pinned Proposal
- **THEN** the backend creates a child Proposal using the selected review guidance and records review-source metadata in the child evolution data.

### Requirement: Frontend Provides A Focused Idea Copilot Panel
The research project page SHALL present Idea Copilot and proposal review guidance as focused panels rather than cramped inline chat.

#### Scenario: User opens Copilot for a Proposal
- **WHEN** the user opens Copilot from a Proposal card
- **THEN** the page shows a panel with markdown-rendered discussion, mode controls, context chips, quick prompts, structured risks/actions/questions, and a send box.

#### Scenario: User creates a new version from Copilot
- **WHEN** Copilot metadata includes or the user enters an evolution focus
- **THEN** the panel offers a create-next-version action that calls the discussion-driven evolution endpoint and refreshes the Proposal list.

#### Scenario: User opens proposal review package
- **WHEN** a Proposal has or can generate reviewer-style review metadata
- **THEN** the page displays the review package with objections, required experiments, revision plan, writing readiness, and a review-guided revision action.
