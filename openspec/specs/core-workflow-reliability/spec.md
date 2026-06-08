# core-workflow-reliability Specification

## Purpose
TBD - created by archiving change core-workflow-stabilization. Update Purpose after archive.
## Requirements
### Requirement: Successful non-streaming LLM calls return generated content
The system SHALL return provider-generated text from a successful non-streaming LLM call and SHALL record token usage when usage information is available.

#### Scenario: Provider returns content on the first attempt
- **WHEN** the configured LLM provider returns a successful completion with text content
- **THEN** the service returns that text content to the caller

#### Scenario: Provider returns usage metadata
- **WHEN** the configured LLM provider returns token usage with a successful completion
- **THEN** the service invokes usage tracking before returning the generated content

### Requirement: Research Idea generation accepts selected paper provenance
The system SHALL consume selected-paper results in the `(paper, score, source)` format throughout research Idea prompt construction and SHALL preserve paper references when storing generated Ideas.

#### Scenario: Selected papers include source metadata
- **WHEN** paper selection returns candidates with paper, relevance score, and source
- **THEN** Idea generation constructs both generation prompts without tuple-unpacking errors

### Requirement: Fixed paper utility endpoints remain reachable
The system SHALL register fixed paper utility endpoints before the dynamic paper-detail endpoint.

#### Scenario: Export all papers as Markdown
- **WHEN** a client requests `GET /api/papers/export-markdown`
- **THEN** the request is handled by the Markdown export endpoint rather than parsed as a paper ID

### Requirement: Paper detail actions target valid resources
The paper detail page SHALL expose only actions backed by a valid paper-specific workflow.

#### Scenario: Paper detail toolbar is rendered
- **WHEN** a user opens a paper detail page
- **THEN** the toolbar does not offer a share action that calls a research-project endpoint with the paper ID

### Requirement: Profile update route is unique
The system SHALL register exactly one `PUT /api/settings/profile` route and SHALL preserve support for updating both email and display name.

#### Scenario: Application routes are loaded
- **WHEN** the FastAPI application registers settings routes
- **THEN** exactly one profile update route is present

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

### Requirement: Paper library surfaces migration health
The paper library maintenance UI SHALL display database migration health using the existing migration health endpoint.

#### Scenario: Database is current
- **WHEN** a user opens the paper-library maintenance view and `/api/health/db` reports `ok`
- **THEN** the UI displays the current and head revisions as healthy.

#### Scenario: Migration is required
- **WHEN** a user opens the paper-library maintenance view and `/api/health/db` reports `migration_required`
- **THEN** the UI displays a warning with the current revision, head revision, and the migration command.
