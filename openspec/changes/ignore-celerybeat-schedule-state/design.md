## Context

The project runs a dedicated `celery-beat` container for scheduled digest delivery. In development, `./backend` is bind-mounted to `/app`, and Celery Beat's default state file path (`celerybeat-schedule`) resolves inside that source tree. The generated GNU dbm state file is currently tracked by Git and changes whenever Beat persists scheduler metadata.

## Goals / Non-Goals

**Goals:**
- Keep Celery Beat runtime state out of source-controlled paths.
- Remove the existing generated state database from Git tracking.
- Preserve the current hourly digest scheduling behavior.

**Non-Goals:**
- Change Celery task registration, timing, or digest delivery logic.
- Introduce a database-backed scheduler.
- Clean unrelated runtime files.

## Decisions

- Use Celery Beat's `--schedule=/tmp/celerybeat-schedule` command option in compose services.
  - Rationale: this is the smallest deployment change and keeps state ephemeral to the container.
  - Alternative considered: setting a Python config value in `celery_app.py`; rejected because the problem is deployment path placement, and the command option is explicit per service.
- Add ignore rules for both root-level and `backend/` Celery Beat state files.
  - Rationale: this protects both current and future local invocation patterns.
- Remove `backend/celerybeat-schedule` from Git tracking without deleting any business code.
  - Rationale: the file is generated scheduler metadata and should not participate in source diffs or commits.

## Risks / Trade-offs

- [Risk] Restarting Celery Beat may lose local scheduler run metadata stored in `/tmp`.
  → Mitigation: the project schedule is declarative in `celery_app.py`; losing local Beat state does not remove the schedule.
- [Risk] A developer running Celery Beat outside Docker can still generate a local schedule file.
  → Mitigation: Git ignore rules cover the common generated filenames.
