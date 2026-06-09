## MODIFIED Requirements

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
