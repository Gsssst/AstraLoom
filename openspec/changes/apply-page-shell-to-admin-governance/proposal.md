## Why

Admin governance is a utility page similar to Settings and Action Center, but it still uses a page-specific gradient hero and generic API failures. It should use the shared page shell and show durable recovery guidance for admin data loading and user updates.

## What Changes

- Wrap Admin page in `PageShell`.
- Move the refresh command into the shell action area.
- Remove the local gradient hero while preserving governance metrics, user table, workspace table, activity timeline, and non-admin warning.
- Use shared API error details for admin data loading and user update failures.
- Display a persistent dismissible Alert for the latest admin failure.

## Capabilities

### New Capabilities

### Modified Capabilities
- `shared-layout-boundaries`: Admin governance pages should use the shared page shell for title, subtitle, actions, and content spacing.
- `api-error-feedback`: Admin governance failures should expose structured recovery guidance.

## Impact

- `frontend/src/pages/AdminPage.tsx`
- Frontend PageShell/admin contract tests.
- No backend API, database, or dependency changes.
