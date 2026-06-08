## ADDED Requirements

### Requirement: Section Creation Uses Database-Compatible Project Identifiers
The manuscript workbench SHALL create sections using project identifiers that are compatible with the database column type.

#### Scenario: Project identifiers are UUID-backed
- **WHEN** a user creates a section for a writing project stored with a UUID project identifier
- **THEN** the section creation query uses a UUID-compatible value
- **AND** the section is persisted without a UUID/string operator error.

### Requirement: Manuscript Workbench Uses Space Efficiently
The manuscript workbench SHALL prioritize active section editing width and group sparse supporting panels together.

#### Scenario: User opens a manuscript project on a wide screen
- **WHEN** the manuscript workbench renders project selection, section navigation, active editor, and evidence cards
- **THEN** the active editor receives the main horizontal space
- **AND** project selection and evidence context are grouped into a compact side rail instead of occupying opposite sides.
