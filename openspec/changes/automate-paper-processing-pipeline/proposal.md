## Why

Paper library ingestion currently leaves several retrieval artifacts behind manual maintenance actions: full text, structured parse, visual evidence/OCR, embeddings, and search index freshness. This makes normal paper use depend on an administrator repeatedly opening a maintenance center, while users only need to know which parts are ready.

## What Changes

- Add an automatic paper-processing reconciler that periodically scans local papers and schedules missing or stale artifacts in bounded batches.
- Trigger the same reconciler after paper ingestion so newly added papers are processed in the background without a manual maintenance click.
- Expose compact processing labels for each paper: full text, structured parse, visual evidence/OCR, embedding, and search index readiness.
- Reposition the maintenance center as an administrator diagnostic/fallback surface rather than the primary daily workflow.
- Keep existing repair endpoints for manual recovery, but normal paper-library usage SHALL not depend on them.

## Capabilities

### New Capabilities

- `paper-processing-automation`: automatic background processing lifecycle for paper-library artifacts.

### Modified Capabilities

- `paper-ingestion`: ingestion must enqueue automatic processing beyond the existing PDF/full-text task.
- `paper-library-maintenance-center`: maintenance UI becomes diagnostic/fallback while normal readiness is shown as labels in the paper library.

## Impact

- Backend services: add an idempotent processing pipeline/reconciler that reuses existing full-text, structured parse, visual evidence, embedding, and BM25/index services.
- Backend tasks: add Celery tasks and beat schedule for post-ingestion and periodic reconciliation.
- Backend API: expose per-paper processing status labels and automation health where needed.
- Frontend: show compact readiness labels in the paper library/detail surfaces and reduce prominent manual maintenance controls.
- Tests: cover pipeline decision logic, ingestion trigger, Celery schedule registration, and paper-library status-label contracts.
