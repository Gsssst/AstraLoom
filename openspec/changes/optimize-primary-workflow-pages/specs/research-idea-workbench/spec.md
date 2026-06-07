## ADDED Requirements

### Requirement: Research Pages Use Work-Focused Shell
The research direction list and research project workbench frontends SHALL present page identity and top-level commands through the shared shell while preserving idea generation and proposal review workflows.

#### Scenario: User opens research direction list
- **WHEN** a user opens the research direction list
- **THEN** the page title, subtitle, and create-direction action are presented by the shared shell
- **AND** project cards, empty state, and create modal remain available.

#### Scenario: User opens research project workbench
- **WHEN** a user opens a research project detail page
- **THEN** the shared shell presents the project title, subtitle, and top-level navigation/generation commands
- **AND** evidence, gap, candidate, proposal, validation, experiment, and modal workflows remain available.
