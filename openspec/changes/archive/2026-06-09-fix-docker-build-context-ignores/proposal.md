## Why

Production Docker builds can fail when local or server-generated directories are copied into image build contexts. In particular, `frontend/node_modules` can overwrite dependencies installed by `npm ci`, causing `tsc: Permission denied` during `npm run build`.

## What Changes

- Add `frontend/.dockerignore` to exclude `node_modules`, `dist`, caches, local env files, and editor/system artifacts from frontend image builds.
- Add `backend/.dockerignore` to exclude uploads, caches, virtual environments, local env files, and test/runtime artifacts from backend image builds.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `deployment-readiness`: Docker image builds shall ignore local runtime/dependency artifacts that can break reproducible server builds.

## Impact

- Affected files: `frontend/.dockerignore`, `backend/.dockerignore`.
- No runtime API, database, or application logic changes.
