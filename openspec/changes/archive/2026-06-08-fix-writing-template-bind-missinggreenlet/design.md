## Context

`bind_submission_profile` calls `update_project(..., metadata_json=metadata)` and expects an updated project dict. `update_project` currently loads `WritingProject` without `selectinload(WritingProject.sections)`, then commits, refreshes, and calls `_project_to_dict(project)`. `_project_to_dict` accesses `project.sections`, which may trigger SQLAlchemy async lazy loading and fail with `MissingGreenlet`.

## Goals / Non-Goals

**Goals:**
- Ensure update serialization uses already-loaded sections.
- Keep the existing endpoint response unchanged.
- Keep the fix scoped to update behavior.

**Non-Goals:**
- Do not change template inspection logic.
- Do not change upload limits or accepted file types.
- Do not redesign project serialization.

## Decisions

1. **Eager-load sections in `update_project`.**
   - Rationale: `get_project` and `list_projects` already use `selectinload`, and `_project_to_dict` expects sections to be available.
   - Alternative: call `get_project` after commit. That would add an extra query and duplicate permission handling.

2. **Avoid a frontend workaround.**
   - Rationale: the failure is a backend serialization bug; the UI already handles the happy path correctly.

## Risks / Trade-offs

- Eager loading sections adds one select for update calls -> acceptable because update responses already include sections.
