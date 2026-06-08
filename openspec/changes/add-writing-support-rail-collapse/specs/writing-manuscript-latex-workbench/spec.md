## ADDED Requirements

### Requirement: Manuscript Support Rail Can Collapse
The manuscript workbench SHALL allow users to collapse and reopen the supporting project/evidence rail.

#### Scenario: User focuses on drafting on a wide screen
- **WHEN** the user collapses the support rail
- **THEN** the project selector and evidence cards are hidden from the main work surface
- **AND** the active manuscript editor receives additional horizontal space
- **AND** a visible reopen control remains available.

#### Scenario: User restores context
- **WHEN** the user reopens the support rail
- **THEN** the project selector and evidence cards return together
- **AND** the active manuscript editor remains available without losing the selected section.
