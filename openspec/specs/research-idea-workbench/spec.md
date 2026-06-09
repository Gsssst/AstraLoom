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

#### Scenario: User starts an idea run with selected toolbox entries
- **WHEN** a user starts an idea generation run with selected toolbox tool IDs and a tool mode
- **THEN** the run config persists the selected tool context
- **AND** candidate generation receives the selected tool names, summaries, use cases, limitations, and linked evidence

#### Scenario: User requires toolbox usage
- **WHEN** the selected tool mode is `required`
- **THEN** generated candidates are prompted to use at least one selected toolbox entry
- **AND** selected proposals record which toolbox entries influenced the candidate when available

#### Scenario: Workbench builds a toolbox fit plan
- **WHEN** a workbench run has selected toolbox entries and a Gap Map
- **THEN** the generation context includes a ranked `tool_fit_plan`
- **AND** each plan item records role, fit score, matched gaps, recommended use, risk note, and rationale

#### Scenario: Toolbox fit plan guides candidate generation
- **WHEN** candidate generation runs with a `tool_fit_plan`
- **THEN** candidate and evolution prompts receive the fit plan
- **AND** fallback candidates use the top-ranked fit item when the model response is unavailable or invalid

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
The system SHALL extract and persist a structured Gap Map before hypothesis generation, SHALL allow users to review selected gaps before continuing proposal generation, and SHALL persist user feedback and refinements on individual gaps.

#### Scenario: Inspect extracted research gaps
- **WHEN** evidence retrieval completes
- **THEN** the run stores research gaps containing the current limitation, evidence references, opportunity, and a testable research question

#### Scenario: Preview gaps without generating proposals
- **WHEN** an authenticated project editor starts a Gap Map preview run
- **THEN** the system persists evidence and Gap Map artifacts and leaves the run in a `gap_review` state without creating proposals.

#### Scenario: Continue from selected gaps
- **WHEN** a project editor submits selected gaps and generation constraints for a reviewed Gap Map run
- **THEN** the system continues proposal generation using those selections and persists the selection metadata on the run.

#### Scenario: Update gap feedback
- **WHEN** a project editor updates one Gap Map item with edited text, quality rating, labels, notes, or evidence references
- **THEN** the system persists the normalized feedback on that gap without creating proposals or recomputing unrelated artifacts.

#### Scenario: Refine one gap
- **WHEN** a project editor requests refinement for one Gap Map item with a focus note
- **THEN** the system updates only that gap using the current evidence and feedback and preserves the run in a reviewable state.

#### Scenario: Inspect gap evidence rationale
- **WHEN** a gap references evidence papers from the Evidence Map
- **THEN** the system exposes enough linked evidence metadata for the interface to show why the gap was extracted.

### Requirement: Multi-path candidate pool
The system SHALL generate a candidate hypothesis pool through gap-grounded, cross-paper inspiration, and user-seed refinement paths.

#### Scenario: Generate candidates from multiple paths
- **WHEN** the workbench has a Gap Map and evidence map
- **THEN** the candidate pool contains structured hypotheses from at least two applicable generation paths

#### Scenario: Candidate is experiment-oriented
- **WHEN** a candidate is stored
- **THEN** it includes a gap, falsifiable hypothesis, approach sketch, evidence references, risks, falsification test, and minimum experiment

#### Scenario: Repair candidates with high novelty collision risk
- **WHEN** a generated candidate is too similar to existing work
- **THEN** the workbench can add a revised candidate that records the nearest collision and avoided facets
- **AND** the revised candidate remains subject to normal review, deduplication, and selection

### Requirement: Explainable deduplication and review
The system SHALL remove substantially overlapping candidates and SHALL review remaining candidates with an explainable multidimensional rubric.

#### Scenario: Merge duplicate hypotheses
- **WHEN** two generated candidates express substantially overlapping hypotheses
- **THEN** the workbench retains the stronger representative and records the duplicate relationship in the run review summary

#### Scenario: Review a candidate
- **WHEN** a unique candidate is reviewed
- **THEN** its review includes novelty, evidence grounding, feasibility, testability, impact, and clarity scores with rationale

#### Scenario: Build facet-level novelty matrix
- **WHEN** the workbench checks a candidate against similar work
- **THEN** the novelty review includes a matrix for research question, mechanism, experiment setup, contribution claim, and evidence overlap
- **AND** the review records nearest collision, similar points, real differences, missing differences, and collision risk

#### Scenario: Penalize weak differentiation
- **WHEN** a candidate has high or medium collision risk without sufficient differentiating facets
- **THEN** quality adjustment and selection ranking reduce its priority with an explainable rationale

### Requirement: Persist top proposals
The system SHALL select and persist top proposals as enriched research ideas compatible with the existing idea discussion, validation, and code-generation flows while preserving selection rationale.

#### Scenario: Complete a successful run
- **WHEN** candidate review finishes successfully
- **THEN** the run enters `complete`, stores its review summary, and persists the selected top proposals with evidence, review, novelty collision, selection rationale, and experiment-plan metadata

#### Scenario: Continue discussing a selected proposal
- **WHEN** the user opens a persisted top proposal
- **THEN** the existing discussion and code-generation actions remain available

#### Scenario: Validate related work from collision metadata
- **WHEN** the user requests validation for a selected proposal with similar-work collision metadata
- **THEN** the validation summary includes those similar works as related-work candidates before falling back to generic evidence ranking.

#### Scenario: Persist proposal toolbox fit rationale
- **WHEN** a selected proposal is influenced by toolbox entries
- **THEN** the proposal review metadata records the relevant tool IDs, tool names, tool-fit plan, and concise tool-fit rationale
- **AND** the research project UI can display that rationale without requiring another generation run

#### Scenario: Persist novelty differentiation metadata
- **WHEN** a selected proposal has novelty matrix metadata
- **THEN** the proposal review metadata records facet scores, nearest collision, differentiation notes, missing differences, and any anti-collision revision source
- **AND** downstream validation can use those fields as related-work context

### Requirement: Research Idea Workbench interface
The system SHALL present the research project page as a workbench that exposes pipeline progress, Evidence Map, Gap Map, candidate pool, selected proposals, proposal-level collision evidence, selection rationale, Gap Map selection controls, and Gap Map feedback controls.

#### Scenario: Inspect intermediate artifacts
- **WHEN** a user opens a project with a completed or running workbench run
- **THEN** the page displays the latest stage and allows the user to inspect available evidence, gaps, candidates, and proposals

#### Scenario: Distinguish score dimensions
- **WHEN** a user views a reviewed proposal
- **THEN** the interface displays review dimensions and rationale rather than only an opaque aggregate score

#### Scenario: Inspect similar work collisions
- **WHEN** a reviewed proposal has novelty collision metadata
- **THEN** the interface displays collision risk, top similar-work entries, their sources, and concise reasons without hiding the existing proposal details.

#### Scenario: Inspect novelty matrix
- **WHEN** a reviewed proposal has facet-level novelty matrix metadata
- **THEN** the interface displays facet risk tags, nearest collision, differentiation notes, and missing differences within the existing proposal detail view

#### Scenario: Inspect selection rationale
- **WHEN** a reviewed proposal has diversity-aware selection metadata
- **THEN** the interface displays why the proposal was selected and the diversity facets it contributes without hiding novelty or adversarial review signals.

#### Scenario: Choose gaps and constraints
- **WHEN** a Gap Map preview run is ready for review
- **THEN** the interface lets the user choose gaps, enter a focus note, and set research mode, risk appetite, and resource budget before continuing generation.

#### Scenario: Edit and label gaps
- **WHEN** a user reviews a Gap Map item
- **THEN** the interface lets the user edit the gap fields, choose quality feedback labels, add notes, and save the feedback.

#### Scenario: Refine gap from user feedback
- **WHEN** a user asks to refine a single Gap Map item
- **THEN** the interface sends that gap and focus note for refinement and refreshes the displayed Gap Map without leaving the review flow.

#### Scenario: View linked evidence for a gap
- **WHEN** a Gap Map item has evidence references
- **THEN** the interface displays linked evidence titles, source categories, and relevance snippets within the gap review context.

### Requirement: Research Workflows Show Persistent API Recovery
The research direction list and research project workbench frontends SHALL show persistent structured recovery guidance for failed project, idea, proposal, evidence, experiment, validation, and generation operations.

#### Scenario: Research direction action fails
- **WHEN** loading, creating, deleting, or seeding a research direction fails
- **THEN** the research direction page displays structured recovery guidance from the shared API error helper.

#### Scenario: Research project workbench action fails
- **WHEN** a research project workbench API operation fails
- **THEN** the project page displays structured recovery guidance while preserving the current workbench state.

#### Scenario: Workbench operation succeeds after failure
- **WHEN** a research operation succeeds after an earlier failed operation
- **THEN** stale research recovery guidance is cleared when appropriate.

### Requirement: Proposal cards expose next-step actions
The research project workbench SHALL show an actionable next-step panel for each persisted proposal using existing proposal evidence, review, experiment, validation, code, discussion, and writing state.

#### Scenario: User opens a proposal card
- **WHEN** a user expands a proposal in the research project workbench
- **THEN** the proposal details include a next-step action panel with concise action labels and rationale
- **AND** the panel includes actions that route into existing proposal workflows without leaving the project context

#### Scenario: Proposal has incomplete follow-up work
- **WHEN** a proposal lacks validation, experiment feedback, generated code, writing handoff, or sufficient evidence
- **THEN** the next-step panel surfaces those missing follow-up actions as available buttons

### Requirement: Gap Map continuation streams long-running generation
The research project workbench SHALL support streaming continuation from a reviewed Gap Map so long-running proposal generation can report progress and avoid frontend request timeout failures.

#### Scenario: Continue generation with progress events
- **WHEN** a user continues proposal generation from a selected Gap Map
- **THEN** the frontend uses a streaming continuation request and applies run, stage, artifact, done, cancelled, and error events as they arrive.

#### Scenario: Preserve synchronous compatibility
- **WHEN** an API client calls the existing non-streaming Gap Map continuation endpoint
- **THEN** the endpoint continues to return the final run response without requiring the streaming client.

#### Scenario: Cancel streaming continuation
- **WHEN** the user stops an in-progress streaming continuation
- **THEN** the frontend aborts the stream and the backend marks the run as cancelled using the existing cancellation behavior.
