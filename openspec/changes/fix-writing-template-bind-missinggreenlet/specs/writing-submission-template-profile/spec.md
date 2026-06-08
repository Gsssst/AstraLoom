## ADDED Requirements

### Requirement: Template profile binding returns updated project safely
The system SHALL return the updated writing project after binding a submission template profile without triggering asynchronous lazy-load failures.

#### Scenario: User binds template to project with sections
- **WHEN** a user binds venue/year and inspected template metadata to a writing project that has sections
- **THEN** the backend response includes the updated project and sections
- **AND** serialization does not attempt unsupported async lazy loading.
