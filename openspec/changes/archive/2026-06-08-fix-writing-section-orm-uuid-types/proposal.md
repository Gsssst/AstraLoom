## Why

Section creation still fails on PostgreSQL because the ORM model declares `writing_sections.project_id` as `String(36)` while the migration and live database use `UUID(as_uuid=True)`. SQLAlchemy therefore compiles UUID comparisons as `VARCHAR` parameters even when the service passes a Python UUID value.

## What Changes

- Align writing ORM foreign key columns with the UUID-backed PostgreSQL schema.
- Ensure section creation and reorder queries compile UUID comparisons as UUID parameters, not `VARCHAR`.
- Apply the same correction to polish version section references so later section-scoped polish history queries do not hit the same mismatch.
- Add regression coverage that inspects model column types and SQL compilation behavior.

## Capabilities

### New Capabilities

### Modified Capabilities

- `writing-manuscript-latex-workbench`: Section persistence must use ORM column types that match UUID-backed writing tables.

## Impact

- Backend ORM: `backend/app/db/models/writing.py`
- Backend services: section creation and polish version queries rely on the corrected model types.
- Tests: writing closed-loop regressions for UUID column typing and compiled SQL binds.
