## Context

The previous service-level fix passed `UUID` values into section creation, but PostgreSQL still received `$1::VARCHAR`. The remaining cause is the SQLAlchemy model: `WritingSection.project_id` and `PolishVersion.section_id` are declared as `String(36)` even though migration `018_create_writing_project_tables.py` created those columns as PostgreSQL UUID foreign keys.

## Goals / Non-Goals

**Goals:**
- Make `WritingSection.project_id` compile as a PostgreSQL UUID bind.
- Make `PolishVersion.section_id` compile as a PostgreSQL UUID bind.
- Preserve API response serialization as strings through existing `_project_to_dict` and response code.
- Avoid database migrations because the live database already has UUID columns.

**Non-Goals:**
- Do not change writing project/user ownership semantics.
- Do not redesign the writing UI.
- Do not modify the existing database schema.

## Decisions

1. **Use `sqlalchemy.dialects.postgresql.UUID(as_uuid=True)` in the writing ORM model.**
   - Rationale: this matches the existing migration and the rest of the codebase's UUID-backed models.
   - Alternative: cast individual query values. That would fix one query but leave the model inconsistent and likely break future joins/filters.

2. **Keep public IDs serialized as strings at API boundaries.**
   - Rationale: frontend contracts and JSON payloads should remain stable.
   - Implementation note: SQLAlchemy entities can carry Python `uuid.UUID`; service serializers already call `str(...)` for IDs.

## Risks / Trade-offs

- [Risk] Tests that assumed string-typed model attributes may need updates.
  -> Mitigation: adjust focused tests to assert UUID column types while preserving API string output.
- [Risk] SQLite-only local behavior can differ from PostgreSQL UUID binding.
  -> Mitigation: add compile-time coverage using the PostgreSQL dialect so the regression targets the production failure mode.
