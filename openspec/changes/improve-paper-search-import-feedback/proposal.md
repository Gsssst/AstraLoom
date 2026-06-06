## Why

Paper search already supports local and multi-provider remote discovery, but search results do not provide enough at-a-glance state about whether a result is local, already saved, newly imported, importable, or missing a stable remote identifier. Users need clearer result filtering and import feedback before sending papers into collections or research directions.

## What Changes

- Add a search-result status filter for all results, local/library results, importable remote results, newly imported results, open-PDF results, and results missing remote identifiers.
- Add a compact result status summary above the paper list.
- Make each result card expose a consistent status tag derived from existing fields and local ingest state.
- Keep existing search providers, ingestion endpoint, collection target, reading actions, and maintenance center behavior unchanged.

## Capabilities

### New Capabilities

### Modified Capabilities
- `paper-discovery-search-and-ingest`: Search results should expose import readiness and post-import state clearly enough for users to filter and act.

## Impact

- Frontend paper-library search UI in `frontend/src/pages/PapersPage.tsx`.
- Frontend contract tests for paper search/import transparency.
- No backend API or database schema changes.
