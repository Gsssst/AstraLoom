## Overview

The processing pipeline stores `queued_steps` when import submits a paper and `running_steps` when a worker starts a step. The current snapshot logic treats both as active, which is useful for the UI but unsafe for worker decisions: a queued step can make the processor believe the artifact is already active and therefore not missing.

This change keeps queued metadata for display but makes execution decisions from artifact readiness after first normalizing metadata.

## Design

1. Add a small metadata reconciliation helper that compares queued/running steps with the current paper artifact snapshot.
2. Remove queued/running markers for steps whose artifacts are already ready.
3. Let queued-only papers remain processable by reconciliation; only fresh `running_steps` should block duplicate processing.
4. In `process_paper`, claim queued work before deciding missing/failed work so the worker sees actual missing artifacts and can execute them.
5. Preserve the existing stale-running TTL behavior for true running steps.

## Risks

- Clearing too much metadata could hide a genuine in-flight task. The implementation only treats `running_steps` as duplicate-protection and only clears ready steps or stale running state.
- A worker may process a queued-only paper while an import-triggered task is about to start. Steps are idempotent and each step marks its own running/completed state, so duplicate submissions should converge without corrupting readiness.

## Verification

- Add tests for queued-only papers being reconciled.
- Add tests for `process_paper` executing missing artifacts even when `queued_steps` exists.
- Add tests for ready artifacts clearing stale running/queued labels.
- Run the targeted backend maintenance tests and strict OpenSpec validation.
