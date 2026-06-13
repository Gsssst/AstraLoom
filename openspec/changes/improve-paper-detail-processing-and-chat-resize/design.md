## Context

The automatic processing pipeline exists, but direct import endpoints still create `Paper` rows outside `PaperIngestionService`. Those papers rely on the periodic reconciler. Runtime inspection also showed a stale Celery worker did not know the new processing tasks until restarted, once restarted the reconciler could be stopped by one PDF containing NUL bytes that PostgreSQL rejects, and repeated Celery runs can reuse asyncpg connections from a previous `asyncio.run()` event loop unless the async SQLAlchemy engine is disposed between tasks. The paper detail page already has resize behavior for PDF/chat layout but not for content/chat layout.

## Goals / Non-Goals

**Goals:**
- New papers from all import paths immediately submit `process_paper_pipeline`.
- A queued marker is persisted when processing is submitted so users can see real queued/running work.
- PDF text and structured metadata are sanitized before persistence.
- Reconciliation continues after one paper fails.
- Repeated Celery processing and reconciliation runs do not fail because of async database connections bound to a closed event loop.
- Visual evidence processing only completes when table OCR/visual summaries are available; missing render assets or OCR prerequisites are exposed as blocking errors.
- The AI Q&A panel can be resized in content-only and PDF layouts.

**Non-Goals:**
- Adding a durable external workflow engine.
- Replacing Celery or changing OCR/table extraction algorithms.
- Adding a new frontend resizable-panel dependency.

## Decisions

1. Keep enqueue logic in a reusable backend helper.
   - Direct endpoints should not duplicate Celery import and metadata handling.
   - The helper writes `queued_steps` metadata before/while submitting the task.

2. Model queued steps separately from active running steps.
   - `running_steps` remains the worker-owned signal.
   - `queued_steps` means work has been submitted and should display as processing until the worker starts or the stale TTL allows recovery.

3. Sanitize recursively at the persistence boundary.
   - PDF text and parser metadata can contain invalid control characters.
   - Cleaning before DB writes avoids one bad PDF aborting the transaction.

4. Roll back failed per-paper work inside reconciliation.
   - Once SQLAlchemy enters rollback state, the batch must call rollback before touching ORM attributes or continuing.

5. Dispose async database connections at the end of Celery paper-processing tasks.
   - Celery worker processes call `asyncio.run()` repeatedly.
   - Disposing the engine after each paper task prevents pooled asyncpg connections from being reused across closed event loops.

6. Use the same visual completeness predicate in scheduling and UI status.
   - A cached visual payload with table items is not enough by itself.
   - Missing table markdown, missing visual summaries, and low-confidence tables keep the visual step incomplete.
   - If assets cannot be generated for OCR, status should show a blocking error instead of silently cycling as generic pending work.

7. Reuse the existing pointer resize implementation.
   - One handle between content and chat is enough for the non-PDF layout.
   - Width is constrained with percentage bounds to preserve usable panels.

## Risks / Trade-offs

- Queued metadata could remain if Redis accepts a task but the worker is offline. Mitigation: the stale-running/queued TTL lets reconciliation recover.
- Sanitizing control characters loses invisible bytes from extracted PDF text. Mitigation: those bytes are not meaningful evidence and cannot be stored in PostgreSQL text/json anyway.
- A local frontend resize implementation is less feature-rich than a library. Mitigation: current page already uses the same pattern successfully for PDF/chat.
