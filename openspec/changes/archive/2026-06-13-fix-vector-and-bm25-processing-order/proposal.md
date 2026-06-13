## Why

The paper artifact pipeline currently runs expensive visual evidence OCR before embeddings, so a paper can display "vector pending" for a long time even though vector generation is quick and independent. BM25 readiness also reports the current backend process cache, while scheduled rebuilds may run in a different worker process, causing the UI to keep showing stale even after the index was rebuilt elsewhere.

## What Changes

- Run embedding and BM25 maintenance before visual evidence when full text and structured parsing are already handled.
- Treat BM25 readiness as database-backed, on-demand-buildable retrieval readiness rather than only current process-local cache state.
- Preserve process-local BM25 caching for actual search performance; search still builds the cache lazily when needed.
- Add regression tests for embedding-before-visual ordering and BM25 status semantics.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `paper-library-maintenance-center`: processing labels and automatic reconciliation must not keep vectors pending behind long visual OCR, and BM25 labels must not depend on whether the current web process has already warmed its local cache.

## Impact

- Affects paper artifact processing order, BM25 status reporting, maintenance health/status labels, and targeted tests.
- No API response shape changes and no new external dependencies.
