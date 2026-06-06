## Why

Celery Beat writes a local schedule state database by default. Because the development compose file bind-mounts `backend/` into the container, the generated `backend/celerybeat-schedule` file is currently tracked by Git and becomes modified whenever the scheduler runs.

## What Changes

- Stop tracking the generated Celery Beat schedule state database.
- Ignore Celery Beat runtime state files in Git.
- Configure Celery Beat services to write their schedule state to `/tmp` instead of the source tree.
- Preserve existing Celery task scheduling behavior.

## Capabilities

### New Capabilities
- `celery-runtime-state`: Celery Beat runtime state is generated outside source-controlled paths and excluded from Git.

### Modified Capabilities

## Impact

- Git tracking for `backend/celerybeat-schedule`.
- Ignore rules in `.gitignore`.
- Celery Beat commands in `docker-compose.yml` and `docker-compose.prod.yml`.
