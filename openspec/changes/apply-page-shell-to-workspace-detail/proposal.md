## Why

The workspace list now uses the shared page shell, but the workspace detail page still has a bespoke outer wrapper and separate back/action header. Aligning the detail page completes the project-space page family and reduces remaining page-level layout drift in low-risk utility areas.

## What Changes

- Wrap workspace detail in `PageShell`.
- Move the back command and module shortcuts into shell actions.
- Keep workspace metadata, progress, launchpad, resource binding, member list, activity timeline, and modals unchanged.
- Use shared API error details for workspace load, candidate load, member, resource binding, and unlink failures.
- Display a persistent dismissible Alert for the latest workspace operation failure.

## Capabilities

### New Capabilities

### Modified Capabilities
- `shared-layout-boundaries`: Workspace detail pages should use the shared page shell for title, subtitle, actions, and content spacing.
- `api-error-feedback`: Workspace detail failures should expose structured recovery guidance.

## Impact

- `frontend/src/pages/WorkspaceDetailPage.tsx`
- Frontend PageShell contract tests.
- No backend API, database, or dependency changes.
