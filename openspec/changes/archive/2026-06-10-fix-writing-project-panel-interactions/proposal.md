## Why

The writing project panel can create duplicate projects because the create modal may not visibly close after submission. Clicking delete or a project card can also lead to a blank page, likely because delete clicks bubble into the project-card selection handler and the parent page keeps rendering a now-deleted selected project.

## What Changes

- Close/reset the create modal immediately after a successful project creation.
- Stop delete-control click propagation from selecting the project card.
- Notify the parent page when the selected project is deleted so dependent writing state is cleared.
- Harden project selection against malformed project payloads.

## Capabilities

### Modified Capabilities
- `writing-manuscript-latex-workbench`: Writing project list interactions remain stable during create, select, and delete actions.

## Impact

- Affected files: `frontend/src/components/writing/WritingProjectPanel.tsx`, `frontend/src/pages/WritingPage.tsx`.
- Affected tests: writing workbench contract test.
- No backend API or database changes.
