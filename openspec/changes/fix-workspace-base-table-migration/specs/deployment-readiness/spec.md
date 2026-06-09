## MODIFIED Requirements

### Requirement: Fresh production database migrations are complete
Fresh production deployments SHALL be able to run Alembic migrations from an empty database to the current head without missing-table failures.

#### Scenario: Workspace tables are migrated on a fresh database
- **WHEN** Alembic runs migration `022` on an empty production database after migrations `001` through `021`
- **THEN** the migration creates `project_spaces` before tables that reference it
- **AND** it creates dependent workspace membership, resource, and activity tables without missing-table failures
