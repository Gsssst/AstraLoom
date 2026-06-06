## Context

Research projects own `research_ideas` and `research_idea_runs`. The database foreign keys use `ON DELETE CASCADE` for project-owned rows, but the ORM relationships do not declare delete cascades or passive database deletes. When a loaded `ResearchProject` is deleted, SQLAlchemy tries to disassociate related `ResearchIdeaRun` rows by setting `project_id = NULL`; PostgreSQL rejects that because `research_idea_runs.project_id` is `NOT NULL`.

## Goals / Non-Goals

**Goals:**
- Let project owners delete research directions that have generated workbench runs, ideas, and evolved child ideas.
- Preserve existing owner-only deletion semantics.
- Add focused regression coverage for the failure mode.

**Non-Goals:**
- No change to workspace member deletion permissions.
- No soft-delete or archive behavior for research projects.
- No database migration, because the existing foreign keys already express cascade/delete-null behavior.

## Decisions

- Configure ORM relationships to match the database delete semantics.
  - `ResearchProject.ideas` and `ResearchProject.idea_runs` use `cascade="all, delete-orphan"` and `passive_deletes=True`.
  - `ResearchIdeaRun.ideas` uses `passive_deletes=True` because `generation_run_id` is nullable and already has `ON DELETE SET NULL`.
  - Add a self-referential children relationship for `ResearchIdea.parent_idea_id` with `passive_deletes=True` so parent deletion relies on the existing `ON DELETE SET NULL`.
- Keep endpoint authorization unchanged by continuing to load projects through `_get_owned_project`.
- Surface backend delete details on the frontend when the API returns them, while retaining the generic fallback.

## Risks / Trade-offs

- [Risk] ORM and database cascade behavior can drift again if future relationships are added without delete semantics. Mitigation: regression test deletes a project with a workbench run and idea.
- [Risk] Database schema in an old environment might lack the expected foreign-key actions. Mitigation: this repo's migrations already define them; no migration is required for current schema.
