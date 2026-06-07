## 1. Migration Status Service

- [x] 1.1 Add a backend service that reads the Alembic code head revision and current database revision.
- [x] 1.2 Add startup logging that reports whether the database schema is current or requires migration.

## 2. API And Startup Integration

- [x] 2.1 Add `GET /api/health/db` with read-only revision status output.
- [x] 2.2 Add a Docker backend startup script that runs `alembic upgrade head` before Uvicorn and wire it into Compose.

## 3. Documentation And Verification

- [x] 3.1 Document manual migration, revision inspection, and migration-health commands.
- [x] 3.2 Add focused backend tests for revision-status classification and run OpenSpec/backend verification.
