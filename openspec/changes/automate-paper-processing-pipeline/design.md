## Context

The current system already has the underlying processors: PDF/full-text loading, structured PDF parsing, document visual evidence extraction with OCR, embedding generation, and BM25 invalidation/rebuild. The missing piece is orchestration. Users are seeing multiple maintenance cards and per-paper repair buttons because the system does not consistently reconcile missing artifacts after a paper enters the library.

Similar GitHub projects use ingestion/indexing as a lifecycle rather than a manual screen. PaperQA2 indexes local PDFs, chunks/caches them, and reuses the built index for later questions. LlamaIndex and Haystack expose ingestion or indexing pipelines made of document loading, transformation, embedding, and indexing steps. This change follows the same lifecycle idea while staying inside the existing app architecture instead of adding a new framework.

## Goals / Non-Goals

**Goals:**

- Automatically process each local paper through the existing artifact steps after ingestion.
- Periodically scan for incomplete papers and resume missing work.
- Keep each run bounded and idempotent so expensive OCR/model calls do not explode.
- Show users simple readiness labels instead of asking them to operate a maintenance center.
- Preserve admin fallback endpoints for diagnostics and retries.

**Non-Goals:**

- Replace the current parser, OCR, embedding, or search implementations.
- Add a new workflow engine or external queue dependency.
- Add user-visible OCR/model configuration toggles.
- Force all existing papers to reprocess immediately in one unbounded run.

## Decisions

1. Add a lightweight backend service for reconciliation.
   - The service computes a per-paper status snapshot for full text, structured parse, visual evidence/OCR, embeddings, and BM25/index freshness.
   - The service exposes pure decision helpers so tests can verify why a paper needs work.

2. Reuse Celery for execution.
   - A post-ingestion task processes a specific paper.
   - A periodic beat task scans a small batch of incomplete papers and enqueues or processes bounded work.
   - Existing single-paper/background visual evidence jobs remain the actual long-running OCR path where possible.

3. Keep the processing order dependency-aware.
   - Full text and local PDF availability come first.
   - Structured parse and visual evidence use the local PDF when available.
   - Embedding generation runs when text is available and embeddings are missing/stale.
   - BM25 is refreshed after textual artifacts change or when the index is stale.

4. Treat maintenance as fallback.
   - The paper library should display readiness labels and a short automation state.
   - Admin maintenance can still diagnose or force repair, but it is not the primary path for normal users.

## Risks / Trade-offs

- [Risk] Visual OCR is slow and can consume model tokens. -> Periodic reconciliation is bounded per run, and ready visual evidence is not reprocessed unless missing, failed, or incomplete.
- [Risk] Multiple processors can touch the same paper. -> Steps are idempotent and status checks run immediately before doing work.
- [Risk] BM25 rebuild can be broader than one paper. -> The reconciler invalidates or triggers rebuild through existing search services and limits frequency through the periodic task.
- [Risk] Existing maintenance UI expectations may change. -> Keep admin diagnostics available, while moving prominent daily controls out of paper/detail surfaces.
