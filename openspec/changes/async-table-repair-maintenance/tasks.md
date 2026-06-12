## 1. Backend Job Contract

- [x] 1.1 Add response models for maintenance job start/status payloads.
- [x] 1.2 Extract low-quality table repair execution into a reusable service with progress callbacks.
- [x] 1.3 Add a status endpoint that normalizes Celery job states into UI-friendly progress data.

## 2. Celery Execution

- [x] 2.1 Register a Celery task that runs bounded low-quality table repair and updates task state.
- [x] 2.2 Change the repair-tables maintenance endpoint to enqueue the task and return immediately.

## 3. Maintenance UI

- [x] 3.1 Update the maintenance-center action runner to handle asynchronous job responses.
- [x] 3.2 Poll active table repair jobs and render progress/final counts instead of timeout errors.

## 4. Verification

- [x] 4.1 Add focused backend tests for enqueue/status normalization and repair progress payloads.
- [x] 4.2 Add or update frontend contract tests for async table repair polling UI behavior.
- [x] 4.3 Run targeted tests, validate the OpenSpec change, and commit the scoped changes.
