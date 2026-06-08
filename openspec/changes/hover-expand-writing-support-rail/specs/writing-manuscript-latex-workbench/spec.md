## MODIFIED Requirements

### Requirement: Manuscript Workbench Is Chapter Driven
The system SHALL provide a manuscript writing workbench organized around paper sections rather than standalone writing tools.

#### Scenario: User opens manuscript writing
- **WHEN** the user opens the manuscript writing mode
- **THEN** the primary surface shows a compact project/evidence rail, section navigation, the active section editor, preview diagnostics, and section AI assistance.

#### Scenario: User selects a section
- **WHEN** the user selects a manuscript section
- **THEN** the editor, preview diagnostics, evidence actions, citation checks, claim safety checks, and AI assistant are scoped to that section.

#### Scenario: User hovers over the project evidence rail
- **WHEN** the desktop user moves the pointer over the compact project/evidence rail
- **THEN** the rail expands to show project and evidence details.

#### Scenario: User leaves the project evidence rail
- **WHEN** the desktop user moves the pointer away from the expanded project/evidence rail
- **THEN** the rail returns to the compact icon-only state.

#### Scenario: User uses the compact rail on touch devices
- **WHEN** hover interaction is unavailable
- **THEN** the compact rail still provides an explicit control to expand project and evidence details.
