## Context

Blank writing projects can have zero sections. The manuscript workbench currently renders a section navigation card and an empty editor state, but neither surface exposes a way to add the first chapter. The backend also lacks a project-scoped section creation endpoint, so the frontend cannot create a section directly.

## Goals / Non-Goals

**Goals:**
- Add a visible chapter creation entry in the manuscript workbench.
- Allow users to create the first section or append another section without leaving the page.
- Select the newly created section immediately.
- Reuse existing `WritingSection` fields and permission rules.

**Non-Goals:**
- Do not add section templates, drag-and-drop outline editing, or bulk chapter generation.
- Do not change the writing section database schema.
- Do not change export behavior.

## Decisions

1. **Create sections through a project-scoped backend endpoint.**
   - Rationale: section creation must verify access to the parent writing project.
   - Alternative: create placeholder sections only in the frontend and persist on edit. That risks losing user work and complicates ordering.

2. **Append new sections after the current max order.**
   - Rationale: predictable and avoids changing existing section order.
   - Alternative: insert after active section. Useful later, but append is sufficient for the empty-state bug.

3. **Expose creation in the section navigation card and editor empty state.**
   - Rationale: users naturally look in the outline/navigation area for chapter management, and the empty state should not be a dead end.

## Risks / Trade-offs

- [Risk] Users may expect rich outline management after seeing an add button.
  → Mitigation: label the action narrowly as adding a chapter/section and keep advanced outline editing for a future change.
- [Risk] Workspace collaborators without edit permission might see a create button that fails.
  → Mitigation: backend enforces permissions; frontend surfaces the API error through existing error feedback.
