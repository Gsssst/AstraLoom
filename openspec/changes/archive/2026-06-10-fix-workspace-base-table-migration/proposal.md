## Why

Fresh production deployments fail during Alembic migration `022` because `project_space_resources` and `project_space_activities` reference `project_spaces`, but no earlier migration creates `project_spaces` or `project_space_members`.

## What Changes

- Update migration `022_create_workspace_resources_activities.py` to create the base project space and membership tables before resource/activity tables.
- Make the migration resilient to a fresh or partially-applied database state by creating missing workspace tables before dependent tables.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `deployment-readiness`: Fresh production database migrations shall create workspace base tables before dependent workspace tables.

## Impact

- Affected file: `backend/alembic/versions/022_create_workspace_resources_activities.py`.
- No API or frontend changes.
- Existing databases already past migration `022` are unaffected unless manually downgraded/replayed.
