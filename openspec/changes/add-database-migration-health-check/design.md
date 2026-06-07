## Context

The backend currently calls `init_db()` during FastAPI startup and the Docker Compose backend command starts Uvicorn directly. Schema changes are managed by Alembic, but startup does not run migrations or expose whether the connected database revision matches the code revision. When a developer pulls new code without running `alembic upgrade head`, feature routes can fail later with missing-column errors.

This change follows the common FastAPI + Alembic Docker pattern used by production templates: run migrations as a startup/prestart step and keep a manual migration command for explicit repair.

## Goals / Non-Goals

**Goals:**
- Run Alembic migrations before the Docker backend starts Uvicorn.
- Expose a read-only database migration health endpoint.
- Log the database revision and code head revision during API startup.
- Document manual migration and drift-check commands.
- Add focused tests for the revision-status logic.

**Non-Goals:**
- Replace Alembic or change existing migration files.
- Automatically repair arbitrary schema drift outside Alembic history.
- Add a frontend database administration UI.
- Change application data models.

## Decisions

### 1. Run migrations before Uvicorn in the backend container

Docker Compose will invoke a shell startup script that runs `alembic upgrade head` and then execs the provided Uvicorn command. This ensures the API does not serve requests against a stale schema.

Alternative considered: run migrations inside FastAPI `lifespan`. Rejected because it would execute in the application process, interact poorly with `--reload`/multi-worker startup, and make migration failures look like application boot errors rather than deployment errors.

### 2. Keep health checks read-only

`GET /api/health/db` will inspect the current `alembic_version` value and the Alembic script head without mutating the database. It returns a degraded status when revisions differ and an error status when the database cannot be inspected.

Alternative considered: have the endpoint trigger migration. Rejected because health checks should be safe, repeatable, and not perform schema writes.

### 3. Use Alembic APIs for code head detection

The implementation will read the code head revision via `alembic.config.Config` and `alembic.script.ScriptDirectory` from the backend Alembic configuration. The database revision will be read from `alembic_version` through the existing async SQLAlchemy engine/session.

Alternative considered: parse migration filenames. Rejected because Alembic already understands branches, heads, and config paths.

### 4. Make missing version table explicit

If `alembic_version` is missing, the health check will return a migration-required status with `current_revision = null` rather than hiding it as a generic database error. Actual connection/query failures still return an error status.

## Risks / Trade-offs

- [Risk] Multiple backend containers could attempt migration simultaneously. -> Mitigation: the current Compose setup has one backend service; Alembic migrations are transactional on PostgreSQL, and failures stop startup clearly.
- [Risk] A manually stamped database may match the head revision while missing a column. -> Mitigation: this change prevents normal revision drift, but deep schema drift still requires manual repair; health output makes revision state visible for diagnosis.
- [Risk] Startup migration increases boot time. -> Mitigation: no-op migrations are fast, and the cost is preferable to late runtime failures.

## Migration Plan

1. Add the startup script and update Docker Compose to use it for the backend service.
2. Add the migration health service and `/api/health/db`.
3. Document manual commands:
   - `docker compose exec backend alembic upgrade head`
   - `docker compose exec backend alembic current`
   - `curl http://127.0.0.1:8000/api/health/db`
4. Existing local databases will be migrated on the next backend container restart; if the schema has non-Alembic drift, the startup migration will fail with Alembic/PostgreSQL output.

## Open Questions

None.
