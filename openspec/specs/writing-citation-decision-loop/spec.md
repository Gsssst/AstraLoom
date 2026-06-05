# writing-citation-decision-loop Specification

## Purpose
TBD - created by archiving change writing-citation-evidence-decision-loop. Update Purpose after archive.
## Requirements
### Requirement: Citation recommendations explain evidence decisions
Citation recommendations SHALL include deterministic decision metadata explaining how the citation should be used in writing.

#### Scenario: User requests citation recommendations
- **WHEN** the user requests citation recommendations for a paragraph
- **THEN** each recommendation includes decision label, decision action, decision warning, role label, match label, and match explanation

### Requirement: Writing UI groups citation recommendations by decision
The writing UI SHALL present citation recommendations as role-aware evidence decisions.

#### Scenario: User reviews citation recommendations
- **WHEN** citation recommendations are returned
- **THEN** the UI shows grouped decision counts and each card explains whether the citation is support, baseline, counterexample, or background evidence

### Requirement: Section citation diagnostics provide next actions
Section citation diagnostics SHALL give actionable next-step guidance for weak, partial, external-only, or missing evidence.

#### Scenario: User checks section citations
- **WHEN** the section citation check returns weak or missing evidence
- **THEN** the UI shows a warning and a concrete next step such as importing the paper, replacing the citation, or adding stronger evidence

