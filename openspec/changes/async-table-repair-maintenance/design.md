## Context

The maintenance center currently calls `POST /papers/maintenance/repair-tables?limit=5` and waits for the whole repair batch. Marker table repair can load models, download HuggingFace artifacts, and parse several PDFs. The browser request can time out while the backend child processes keep running; repeated clicks then create overlapping parser processes.

GitHub research: FastAPI/Celery examples such as `GregaVrbancic/fastapi-celery`, `testdrivenio/fastapi-celery`, and `Fuad-Haque/task-automation-api` use the same basic pattern for long-running work: enqueue a background task, return a task/job id immediately, and let clients poll a status endpoint for progress and result. This project already has Celery and Redis, so the iteration should reuse that pattern instead of adding a new worker system.

## Goals / Non-Goals

**Goals:**

- Prevent the maintenance UI from surfacing HTTP timeout errors for Marker table repair.
- Track low-quality table repair as a bounded job with progress, current paper, counts, and errors.
- Keep the existing admin-only authorization and bounded `limit`.
- Reuse the existing Celery/Redis deployment.

**Non-Goals:**

- Convert every maintenance action to async in this iteration.
- Add a persistent database table for maintenance jobs.
- Add task cancellation or historical job browsing beyond the active/latest job returned by Celery.
- Change table quality detection or Marker parsing behavior.

## Decisions

1. Use Celery task state as the job store.
   - `repair-tables` returns a Celery task id and an initial status payload.
   - `GET /papers/maintenance/jobs/{job_id}` reads `AsyncResult` and returns normalized status.
   - Rationale: Redis result backend is already configured and avoids a migration.
   - Alternative considered: add `maintenance_jobs` table. Deferred until we need durable history, cancellation, or multi-user job lists.

2. Extract repair execution into a service function shared by FastAPI and Celery.
   - The existing synchronous repair loop becomes a reusable function that accepts a progress callback.
   - Rationale: the endpoint and worker must not drift in candidate selection, counting, or error formatting.

3. Make only low-quality table repair async in this change.
   - Rationale: it is the action currently proven to exceed the client timeout and leave parser subprocesses behind.
   - Other maintenance actions can later adopt the same job envelope after this path is validated.

4. Poll from the maintenance UI.
   - The UI starts the repair job, stores the returned job id, polls every few seconds, shows progress, and refreshes the maintenance center after terminal states.
   - Rationale: polling is simpler and more reliable than SSE/WebSocket for the existing maintenance panel.

## Risks / Trade-offs

- [Risk] Celery result entries expire after backend retention. -> Show active job status while polling; durable job history is out of scope.
- [Risk] Multiple admins can start overlapping repair jobs. -> The UI disables the current action while its job is active; backend duplicate prevention can be added later if this becomes a real operational issue.
- [Risk] Worker restarts can mark tasks failed without detailed per-paper state. -> Normalize Celery failure into a clear error payload.
- [Risk] Existing orphan Marker processes may remain from previous synchronous attempts. -> This iteration prevents new timeout-driven orphaning; operators may still need to stop old processes once during deployment.
