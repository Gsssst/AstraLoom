## Why

Action Center is a workflow hub, but it still uses a page-specific gradient hero and generic failure messages. It should adopt the shared page shell and show durable recovery details when loading or executing actions fails.

## What Changes

- Wrap Action Center in `PageShell`.
- Keep the action summary as normal content cards instead of embedding it in the page hero.
- Use shared API error details for load and execution failures.
- Persist execution/load failure feedback in an Alert while keeping success result feedback intact.

## Capabilities

### New Capabilities

### Modified Capabilities
- `shared-layout-boundaries`: Action Center should use the shared page shell for page title and content spacing.
- `api-error-feedback`: Action Center load and execution failures should expose structured recovery guidance.

## Impact

- `frontend/src/pages/ActionCenterPage.tsx`
- Frontend PageShell/action center contract tests.
- No backend API, database, or dependency changes.
