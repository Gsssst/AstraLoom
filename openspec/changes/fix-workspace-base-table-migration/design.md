## Context

The workspace ORM includes `ProjectSpace`, `ProjectSpaceMember`, `ProjectSpaceResource`, and `ProjectSpaceActivity`. Migration `022` only creates resource and activity tables, both of which have foreign keys to `project_spaces`. On a new PostgreSQL volume, Alembic reaches `022` and fails with `relation "project_spaces" does not exist`.

## Decision

Add creation of `project_spaces` and `project_space_members` to migration `022`, before dependent tables. Use SQLAlchemy's inspector to avoid recreating tables if a server reached a partial state or if an operator manually created one of the tables during recovery.

## Recovery Notes

If `022` failed before any table was created, operators can pull this fix and rerun `alembic upgrade head`. If some workspace tables were created manually, the migration checks existing table names and only creates missing tables.

## Non-Goals

- No model changes.
- No data migration for existing workspace rows.
- No rewrite of the migration chain.

## Validation

- Run OpenSpec validation.
- Run focused migration syntax checks.
- Run `git diff --check`.
