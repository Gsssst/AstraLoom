## Why

The manuscript workbench empty state tells users to create chapters, but the UI has no visible chapter creation entry. Blank writing projects therefore land on a dead end: the section editor cannot be opened because there are zero sections, and users cannot discover where to add one.

## What Changes

- Add an explicit chapter creation action inside the manuscript section navigation and empty state.
- Add a backend endpoint/service method to create a writing section in an existing project, respecting project ownership/workspace edit permissions.
- After creation, select the new section immediately so users can start writing LaTeX source.
- Keep the feature scoped to writing sections; no database schema change is required.

## Capabilities

### New Capabilities

### Modified Capabilities

- `writing-manuscript-latex-workbench`: The chapter-driven manuscript workbench must provide a visible way to create the first section and additional sections.

## Impact

- Backend: `writing_v2.py`, `writing_project_service.py`, writing closed-loop tests.
- Frontend: `WritingPage.tsx`, writing workbench contract tests.
- OpenSpec: delta for `writing-manuscript-latex-workbench`.
