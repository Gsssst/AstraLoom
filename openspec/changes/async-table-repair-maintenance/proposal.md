## Why

The low-quality table repair maintenance action can now start Marker, but it still runs inside the HTTP request. Marker may load or download models and process PDFs for several minutes, so the browser request times out while orphan parser processes keep running and repeated clicks stack more repairs.

## What Changes

- Add an asynchronous maintenance job path for low-quality table repair.
- Return a job id immediately when the maintenance center starts table repair.
- Expose a job-status endpoint with progress, counts, current paper, errors, and final result.
- Update the maintenance UI to poll the job instead of showing a timeout failure while work continues.
- Preserve the existing bounded repair behavior and admin-only access.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `knowledge-base-retrieval-maintenance`: Low-quality table repair runs as a tracked asynchronous maintenance job instead of a long synchronous request from the maintenance UI.

## Impact

- Affects paper maintenance APIs, Celery task registration, frontend maintenance-center action handling, and focused backend/frontend tests.
- Reuses the existing Redis/Celery stack and Marker parser runtime.
- Does not add a database migration or change paper metadata schema.
