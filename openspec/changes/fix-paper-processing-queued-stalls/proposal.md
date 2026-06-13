## Why

Some imported papers remain labeled as queued or processing even when Celery has no active, reserved, or scheduled task. This blocks the automatic paper artifact lifecycle and makes users unable to tell whether a paper is genuinely being processed.

## What Changes

- Separate scheduler/UI queue metadata from worker work selection so queued labels do not hide missing artifacts from the actual processor.
- Clear stale or already-satisfied running/queued steps before processing and during reconciliation candidate selection.
- Keep fresh real running steps protected from duplicate processing, while allowing queued-only papers to be picked up by reconciliation.
- Add regression coverage for queued-only stalls and ready-artifact running markers.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `paper-library-maintenance-center`: automatic processing status and reconciliation must recover from queued/running metadata that no longer corresponds to real unfinished work.

## Impact

- Affects backend paper processing orchestration, status snapshots, reconciliation selection, and targeted tests.
- No API shape changes and no new external dependencies.
