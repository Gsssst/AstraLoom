## ADDED Requirements

### Requirement: Writing Section ORM Types Match UUID Schema
The manuscript workbench SHALL map UUID-backed writing section foreign keys using UUID-compatible ORM column types.

#### Scenario: Section creation compiles a project filter
- **WHEN** the backend builds the section creation query for a UUID-backed writing project
- **THEN** the `writing_sections.project_id` comparison is compiled as a UUID-compatible bind
- **AND** PostgreSQL does not receive a `VARCHAR` bind for the UUID column.

#### Scenario: Section polish history compiles a section filter
- **WHEN** the backend builds a polish history query for a UUID-backed writing section
- **THEN** the `polish_versions.section_id` comparison is compiled as a UUID-compatible bind
- **AND** PostgreSQL does not receive a `VARCHAR` bind for the UUID column.
