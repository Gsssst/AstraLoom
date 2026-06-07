## ADDED Requirements

### Requirement: Database migration status is observable
The system SHALL expose a read-only database health endpoint that reports the connected database Alembic revision, the code head revision, and whether the database is current.

#### Scenario: Database revision matches code head
- **WHEN** a client requests `GET /api/health/db` and the database revision equals the code head revision
- **THEN** the response indicates status `ok`, includes both revisions, and marks `is_current` as true

#### Scenario: Database revision does not match code head
- **WHEN** a client requests `GET /api/health/db` and the database revision is missing or behind the code head revision
- **THEN** the response indicates status `migration_required`, includes the current and head revisions, and marks `is_current` as false

### Requirement: Backend startup surfaces migration drift
The system SHALL report database migration status during API startup before serving normal feature workflows.

#### Scenario: Startup detects a current database
- **WHEN** the API starts and the database revision matches the code head revision
- **THEN** the startup log records that the database schema is current

#### Scenario: Startup detects migration drift
- **WHEN** the API starts and the database revision does not match the code head revision
- **THEN** the startup log records the current revision, head revision, and the need to run migrations

### Requirement: Docker backend startup applies Alembic migrations
The Docker backend service SHALL run `alembic upgrade head` before starting Uvicorn.

#### Scenario: Backend container starts
- **WHEN** the Docker backend service starts after PostgreSQL is healthy
- **THEN** it runs Alembic migrations before executing the Uvicorn application command

#### Scenario: Migration fails during container startup
- **WHEN** Alembic migration fails during Docker backend startup
- **THEN** the backend service does not start Uvicorn and exits with the migration failure

### Requirement: Operators can run migration checks manually
The project documentation SHALL include commands for manually applying migrations and checking migration health.

#### Scenario: Developer troubleshoots schema drift
- **WHEN** a developer reads the project setup or troubleshooting documentation
- **THEN** they can find commands to run Alembic migration, inspect the current revision, and call the migration health endpoint
