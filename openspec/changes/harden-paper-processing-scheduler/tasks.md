## 1. Scheduler Locking

- [x] 1.1 Add a Redis-backed singleton lock helper for paper processing reconciliation.
- [x] 1.2 Wrap `reconcile_paper_processing` so overlapping scheduled runs return a locked/skipped summary without processing papers.
- [x] 1.3 Ensure lock ownership is released after success or failure.

## 2. Running-State Recovery

- [x] 2.1 Add helpers to classify fresh vs stale `running_steps` metadata.
- [x] 2.2 Skip fresh-running papers during reconciliation candidate selection.
- [x] 2.3 Clear stale running metadata before retrying a paper.

## 3. Verification

- [x] 3.1 Add tests for singleton lock behavior.
- [x] 3.2 Add tests for fresh-running skip and stale-running retry.
- [x] 3.3 Run targeted backend tests and OpenSpec validation.
