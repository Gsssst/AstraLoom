## Context

`WritingSection.project_id` is UUID-backed in the production PostgreSQL schema. The new section creation path used `str(project.id)` in a filter against that column, causing asyncpg to reject the query with `operator does not exist: uuid = character varying`. The page layout also keeps the project selector on the far left and evidence cards on the far right, which makes the editor feel narrow while side content is sparse.

## Goals / Non-Goals

**Goals:**
- Use UUID-typed values when filtering or writing section `project_id`.
- Preserve existing workspace edit permission checks.
- Compact side panels so project selection and evidence cards share one side column.
- Give the active LaTeX section editor more horizontal room.

**Non-Goals:**
- Do not change the database schema.
- Do not redesign every writing workflow tab.
- Do not add drag-and-drop outline management.

## Decisions

1. **Bind UUID values directly for section creation queries.**
   - Rationale: this matches PostgreSQL column type and avoids implicit casts.
   - Alternative: cast the column or parameter in SQL. That is less portable and unnecessary with SQLAlchemy UUID values.

2. **Use one compact side rail for project and evidence panels.**
   - Rationale: the active editor is the primary work surface; project selection and evidence are supporting context.
   - Alternative: keep three columns. That wastes space for sparse projects and makes the editor feel constrained.

## Risks / Trade-offs

- [Risk] Existing SQLite/dev schemas may tolerate string UUIDs differently.
  → Mitigation: SQLAlchemy UUID values continue to work with the configured model layer and match production PostgreSQL.
- [Risk] A single side rail can grow tall.
  → Mitigation: keep panels stacked with internal scrolling where evidence can become long.
