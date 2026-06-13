## Why

The paper library can render a blank screen after the visual evidence progress update because a React hook dependency references a callback before that callback is initialized. This is a runtime initialization error in the page component.

## What Changes

- Move maintenance job helper callbacks before the polling effect that uses them.
- Add frontend contract coverage to prevent helper-order regressions.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-library-maintenance-center`: The paper library maintenance page must render reliably while polling visual evidence jobs.

## Impact

- Frontend: `PapersPage.tsx` helper ordering.
- Tests: frontend contract regression.
