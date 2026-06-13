## Overview

The pipeline steps are independent after full text and structured parsing. Visual evidence is the slowest step because it may render PDF pages and call a vision-capable model. Embedding generation and BM25 rebuilds should happen before that slow step so search readiness improves quickly.

BM25 is implemented as a process-local cache. That is acceptable for retrieval, because each process can lazily build its own cache before search. It is not acceptable as a global readiness label, because worker and web processes do not share memory.

## Design

1. Reorder `PaperProcessingPipeline.process_paper` so it runs:
   - full text
   - structured parse
   - embedding
   - BM25 rebuild
   - visual evidence
2. Keep per-step idempotency and `max_steps` accounting unchanged.
3. Add a database-backed BM25 readiness helper on `HybridSearchService`.
   - If the database has papers, BM25 is ready from a product perspective because the process can build the cache on demand.
   - Include process-local cache fields so diagnostics can still show whether the current process is warmed.
4. Let `paper_processing_snapshot` optionally receive this database-backed status from API/reconciliation code; keep fallback process-local status for pure in-memory tests and call sites without a session.

## Risks

- Moving visual evidence later means a single scheduled batch may show visual evidence pending for longer, but it unblocks vector search faster and keeps the expensive step last.
- Marking BM25 ready when the process cache is cold may hide warmup cost, but actual BM25 search already calls `_ensure_bm25_index()` and builds before returning results.

## Verification

- Add unit tests that embedding is attempted before visual evidence when both are missing.
- Add tests that BM25 database-backed status reports ready even when the current process-local cache is cold.
- Run targeted backend tests and OpenSpec validation.
