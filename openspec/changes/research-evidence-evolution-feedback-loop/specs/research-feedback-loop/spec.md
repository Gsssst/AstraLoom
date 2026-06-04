## ADDED Requirements

### Requirement: External evidence can be imported into the project library

The system SHALL allow a project owner to import an external evidence item from the latest workbench run into the local paper library.

#### Scenario: External paper is imported

- **WHEN** the owner imports an external evidence item
- **THEN** the system reuses paper-ingestion deduplication
- **AND** associates the resulting local paper ID with the current research project
- **AND** returns whether the paper was newly created

### Requirement: Proposal evolution is traceable across multiple rounds

The system SHALL preserve each Proposal version and expose its connected lineage.

#### Scenario: A child Proposal is evolved again

- **WHEN** the owner evolves an already evolved Proposal
- **THEN** the new child records its parent Proposal ID
- **AND** increments the evolution round
- **AND** leaves prior versions unchanged

#### Scenario: Lineage is requested

- **WHEN** the owner requests a Proposal lineage
- **THEN** the system returns connected ancestor and descendant versions

### Requirement: Experiment feedback can drive the next Proposal version

The system SHALL support experiments linked to a Proposal and use their feedback during evolution.

#### Scenario: Linked experiment is saved

- **WHEN** the owner records an experiment for a Proposal
- **THEN** the system stores a stable experiment ID, Proposal ID, results and notes

#### Scenario: Feedback evolution is requested

- **WHEN** the owner selects a linked experiment to drive evolution
- **THEN** the system creates a traceable child Proposal
- **AND** includes the selected experiment feedback in the evolution context

