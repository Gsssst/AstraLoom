## MODIFIED Requirements

### Requirement: Structured Gap Map
The system SHALL extract and persist a structured Gap Map before hypothesis generation and SHALL allow users to review selected gaps before continuing proposal generation.

#### Scenario: Inspect extracted research gaps
- **WHEN** evidence retrieval completes
- **THEN** the run stores research gaps containing the current limitation, evidence references, opportunity, and a testable research question

#### Scenario: Preview gaps without generating proposals
- **WHEN** an authenticated project editor starts a Gap Map preview run
- **THEN** the system persists evidence and Gap Map artifacts and leaves the run in a `gap_review` state without creating proposals.

#### Scenario: Continue from selected gaps
- **WHEN** a project editor submits selected gaps and generation constraints for a reviewed Gap Map run
- **THEN** the system continues proposal generation using those selections and persists the selection metadata on the run.

### Requirement: Research Idea Workbench interface
The system SHALL present the research project page as a workbench that exposes pipeline progress, Evidence Map, Gap Map, candidate pool, selected proposals, proposal-level collision evidence, selection rationale, and Gap Map selection controls.

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
