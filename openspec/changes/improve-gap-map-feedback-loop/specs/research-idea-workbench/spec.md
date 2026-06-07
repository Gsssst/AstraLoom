## MODIFIED Requirements

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
