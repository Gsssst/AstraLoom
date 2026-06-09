## Context

The frontend API client defaults to a 30-second timeout. Maintenance actions run synchronously today. Embedding backfill invokes a local sentence-transformers model; the first call can spend significant time downloading/loading the model before encoding papers.

## Decision

Set a 5-minute timeout for maintenance POST actions. This matches existing long-running export/report actions that already use explicit longer timeouts, while keeping normal API calls at the default timeout.

## Non-Goals

- No background job redesign.
- No new progress polling UI.
- No backend async queue migration for embedding generation.

## Validation

- Run OpenSpec validation.
- Run TypeScript build or targeted static checks where practical.
- Run `git diff --check`.
