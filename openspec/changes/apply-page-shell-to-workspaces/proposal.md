## Why

`PageShell` now exists, but only Settings has adopted it. The project-space list is another low-risk page with its own hero and action placement, so converting it next will prove the shared shell works for list pages with primary actions.

## What Changes

- Wrap the Workspaces page in `PageShell`.
- Move the “新建空间” action into the page shell action area.
- Remove the page-specific gradient hero while preserving the workspace list, creation modal, cards, resource counts, and navigation.

## Capabilities

### New Capabilities

### Modified Capabilities
- `shared-layout-boundaries`: Project-space list pages should be able to adopt the shared page shell while preserving page actions.

## Impact

- `frontend/src/pages/WorkspacesPage.tsx`
- Frontend PageShell contract tests.
- No backend API, database, or dependency changes.
