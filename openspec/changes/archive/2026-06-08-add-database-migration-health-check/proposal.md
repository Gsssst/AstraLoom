## Why

Recent research-workflow changes added database columns, but the running database was not migrated before the API started. That allowed the UI to load into runtime `UndefinedColumnError` failures instead of surfacing a clear migration state.

## What Changes

- Add a database migration health check that reports the database Alembic revision, code head revision, and whether they match.
- Log migration status during API startup so mismatches are visible before feature endpoints fail.
- Update Docker backend startup to run Alembic migrations before Uvicorn starts.
- Document manual migration and migration-health troubleshooting commands.

## Capabilities

### New Capabilities

### Modified Capabilities

- `core-workflow-reliability`: Core service startup shall prevent or clearly expose database migration drift before user workflows hit missing-column errors.

## Impact

- Backend API health surface: `GET /api/health/db`
- Backend startup logging and Docker Compose backend command
- Alembic revision inspection utilities
- README operational commands
