## ADDED Requirements

### Requirement: Paper library surfaces migration health
The paper library maintenance UI SHALL display database migration health using the existing migration health endpoint.

#### Scenario: Database is current
- **WHEN** a user opens the paper-library maintenance view and `/api/health/db` reports `ok`
- **THEN** the UI displays the current and head revisions as healthy.

#### Scenario: Migration is required
- **WHEN** a user opens the paper-library maintenance view and `/api/health/db` reports `migration_required`
- **THEN** the UI displays a warning with the current revision, head revision, and the migration command.
