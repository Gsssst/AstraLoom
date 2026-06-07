## Why

The paper digest inbox is an independent notification/list page with its own gradient header and generic action failures. It should follow the same shared page shell pattern as Settings, Workspaces, and Action Center, and failed digest actions should provide durable recovery guidance.

## What Changes

- Wrap the paper digest inbox in `PageShell`.
- Move the return-to-paper-library action into the shell action area.
- Remove the local gradient hero while preserving digest history, unread summary, paper actions, and empty state.
- Use shared API error details for digest load, read-all, ingest, reading-status, and feedback failures.
- Display a persistent dismissible Alert for the latest digest action failure.

## Capabilities

### New Capabilities

### Modified Capabilities
- `shared-layout-boundaries`: Paper digest inbox pages should use the shared page shell for title, subtitle, actions, and content spacing.
- `api-error-feedback`: Paper digest inbox failures should expose structured recovery guidance.

## Impact

- `frontend/src/pages/PaperDigestInboxPage.tsx`
- Frontend PageShell contract tests.
- No backend API, database, or dependency changes.
