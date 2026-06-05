# research-idea-workbench Specification

## Purpose
TBD - created by archiving change research-idea-workbench-v2. Update Purpose after archive.
## Requirements
### Requirement: Project-owned staged idea run
The system SHALL allow an authenticated project owner to start a persisted Research Idea Workbench run and SHALL track its stage, progress, configuration, intermediate artifacts, completion status, and error details.

#### Scenario: Start a workbench run
- **WHEN** an authenticated owner starts a run for one of their research projects
- **THEN** the system creates a persisted run in the `briefing` stage and begins the staged pipeline

#### Scenario: Deny access to another user's run
- **WHEN** an authenticated user requests a run that belongs to another user's project
- **THEN** the system returns a not-found response without exposing run contents

### Requirement: Visible run progress
The system SHALL provide a stream of workbench progress events and SHALL allow a browser refresh to recover the latest persisted run state.

#### Scenario: Receive stage progress
- **WHEN** a running pipeline advances from evidence retrieval to Gap Map extraction
- **THEN** the progress stream emits the new stage, percentage, and user-readable message

#### Scenario: Recover after refresh
- **WHEN** the user reloads a project page after a run has started
- **THEN** the page can request the persisted run detail and display its latest artifacts and status

### Requirement: Evidence map
The system SHALL construct an inspectable evidence map from project-attached papers and local-library matches and SHALL classify evidence items as seed, background, or inspiration papers.

#### Scenario: Include manually attached papers
- **WHEN** a project has explicitly attached paper identifiers
- **THEN** those papers appear in the evidence map as seed papers with provenance

#### Scenario: Explain evidence relevance
- **WHEN** the workbench stores an evidence item
- **THEN** the item includes its paper identity, title, abstract excerpt, category, and relevance explanation

### Requirement: Structured Gap Map
The system SHALL extract and persist a structured Gap Map before hypothesis generation.

#### Scenario: Inspect extracted research gaps
- **WHEN** evidence retrieval completes
- **THEN** the run stores research gaps containing the current limitation, evidence references, opportunity, and a testable research question

### Requirement: Multi-path candidate pool
The system SHALL generate a candidate hypothesis pool through gap-grounded, cross-paper inspiration, and user-seed refinement paths.

#### Scenario: Generate candidates from multiple paths
- **WHEN** the workbench has a Gap Map and evidence map
- **THEN** the candidate pool contains structured hypotheses from at least two applicable generation paths

#### Scenario: Candidate is experiment-oriented
- **WHEN** a candidate is stored
- **THEN** it includes a gap, falsifiable hypothesis, approach sketch, evidence references, risks, falsification test, and minimum experiment

### Requirement: Explainable deduplication and review
The system SHALL remove substantially overlapping candidates and SHALL review remaining candidates with an explainable multidimensional rubric.

#### Scenario: Merge duplicate hypotheses
- **WHEN** two generated candidates express substantially overlapping hypotheses
- **THEN** the workbench retains the stronger representative and records the duplicate relationship in the run review summary

#### Scenario: Review a candidate
- **WHEN** a unique candidate is reviewed
- **THEN** its review includes novelty, evidence grounding, feasibility, testability, impact, and clarity scores with rationale

### Requirement: Persist top proposals
The system SHALL select and persist top proposals as enriched research ideas compatible with the existing idea discussion and code-generation flows.

#### Scenario: Complete a successful run
- **WHEN** candidate review finishes successfully
- **THEN** the run enters `complete`, stores its review summary, and persists the selected top proposals with evidence, review, and experiment-plan metadata

#### Scenario: Continue discussing a selected proposal
- **WHEN** the user opens a persisted top proposal
- **THEN** the existing discussion and code-generation actions remain available

### Requirement: Research Idea Workbench interface
The system SHALL present the research project page as a workbench that exposes pipeline progress, Evidence Map, Gap Map, candidate pool, and selected proposals.

#### Scenario: Inspect intermediate artifacts
- **WHEN** a user opens a project with a completed or running workbench run
- **THEN** the page displays the latest stage and allows the user to inspect available evidence, gaps, candidates, and proposals

#### Scenario: Distinguish score dimensions
- **WHEN** a user views a reviewed proposal
- **THEN** the interface displays review dimensions and rationale rather than only an opaque aggregate score

