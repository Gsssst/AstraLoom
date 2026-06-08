## Why

Creating the first manuscript section fails in PostgreSQL because section creation compares a UUID column with a string parameter. The manuscript workbench layout also wastes horizontal space by separating project selection and evidence into distant columns even when both panels have little content.

## What Changes

- Fix section creation to query and write `WritingSection.project_id` using the same UUID type as the database column.
- Add regression coverage for the UUID-safe section creation query.
- Rebalance the manuscript workbench so project selection and evidence cards can sit together in a compact side panel while the section editor gets more useful width.
- Keep the new section creation UX and LaTeX editor behavior intact.

## Capabilities

### New Capabilities

### Modified Capabilities

- `writing-manuscript-latex-workbench`: Section creation must work reliably on UUID-backed databases, and the workbench layout must use horizontal space efficiently.

## Impact

- Backend: `writing_project_service.py`, writing closed-loop tests.
- Frontend: `WritingPage.tsx`, writing workbench contract tests.
- OpenSpec: delta for `writing-manuscript-latex-workbench`.
