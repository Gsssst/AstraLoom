## Why

Paper processing now includes slow steps such as visual evidence extraction and OCR. The periodic reconciler can overlap with an earlier run or reselect papers already marked as running, which risks duplicate long-running work and confusing readiness labels.

## What Changes

- Add scheduler-level protection so only one paper processing reconciliation run is active at a time.
- Teach the reconciler to skip papers with fresh `running_steps` metadata and to retry only after a bounded stale-running timeout.
- Preserve simple paper labels for users: running papers remain visible as processing, stale work can recover automatically, and failed work is still surfaced.
- Add tests for overlap prevention, fresh-running skips, stale-running retries, and metadata cleanup.

## Capabilities

### New Capabilities
- `paper-processing-scheduler-reliability`: Reliable background scheduling behavior for long-running paper processing artifacts.

### Modified Capabilities

## Impact

- Backend paper processing orchestration in `backend/app/services/paper_processing_pipeline.py`.
- Celery task behavior in `backend/app/tasks/paper_tasks.py`.
- Tests covering automatic paper processing and visual evidence backfill behavior.
- No new external runtime dependency; reuse the existing Celery/Redis stack when available.
