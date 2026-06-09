## Why

Knowledge maintenance actions such as embedding backfill can exceed the frontend's default 30-second Axios timeout, especially on fresh server deployments where the local sentence-transformers model must be downloaded and loaded for the first time.

## What Changes

- Increase frontend timeout for knowledge maintenance POST actions.
- Apply the longer timeout in both the paper maintenance center and settings maintenance panel.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `knowledge-base-retrieval-maintenance`: Maintenance actions shall allow long-running embedding/full-text operations to complete instead of failing at the default UI timeout.

## Impact

- Affected files: `frontend/src/pages/PapersPage.tsx`, `frontend/src/pages/SettingsPage.tsx`.
- No backend behavior, database, or API contract changes.
