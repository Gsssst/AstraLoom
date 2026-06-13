## Context

The paper processing pipeline is idempotent, but some steps are expensive: structured parsing, visual evidence extraction, table OCR, embeddings, and BM25 rebuilds. Celery Beat currently schedules reconciliation every 10 minutes with a bounded batch. If a previous reconciliation run is still active, a later run can start and inspect the same papers. Individual papers record `running_steps`, but the scheduler does not yet use that metadata as a concurrency guard.

## Goals / Non-Goals

**Goals:**
- Prevent overlapping reconciliation runs from doing duplicate work.
- Skip papers that have fresh running metadata while keeping their UI state as processing.
- Automatically recover stale running metadata after a bounded timeout.
- Keep the implementation dependency-free beyond the existing Celery/Redis stack.

**Non-Goals:**
- Replacing Celery with a durable workflow engine.
- Adding a user-facing maintenance dashboard for queues.
- Changing the visual evidence extraction algorithm or OCR prompt format.

## Decisions

1. Use a Redis-backed singleton lock for `reconcile_paper_processing` when Redis is available.
   - Rationale: The project already requires Redis for Celery broker/backend, and Redis `SET NX EX` is the same pattern used by common Celery singleton libraries.
   - Alternative considered: Add `celery-singleton` or `celery-once`. Rejected to avoid new dependencies and migration work for a narrow lock.
   - Fallback: If Redis locking is unavailable, the task still runs and logs the lock issue rather than disabling processing.

2. Treat `running_steps` as fresh only when `last_checked_at` is newer than a configured TTL.
   - Rationale: A worker crash could leave `running_steps` forever. TTL allows recovery while still preventing duplicate work during normal long-running tasks.
   - Default: two hours, long enough for visual evidence OCR batches but short enough to retry stuck work.

3. Filter fresh-running papers during candidate selection.
   - Rationale: This avoids wasting the limited batch size on papers that another task is already processing.
   - Stale running metadata is cleared before retry so the paper label no longer remains stuck.

## Risks / Trade-offs

- Redis outage → the singleton lock cannot be acquired reliably. Mitigation: log and continue, preserving availability over perfect deduplication.
- Very slow OCR longer than the TTL could be retried. Mitigation: default TTL is conservative and configurable in code-level constants.
- Process-local fallback locks do not coordinate across multiple worker processes. Mitigation: Redis remains the primary mechanism in deployed Celery environments.
