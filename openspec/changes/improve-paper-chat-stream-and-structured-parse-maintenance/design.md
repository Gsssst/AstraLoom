## Context

The current paper chat stream appends backend `error` frames as ordinary answer content. That is correct for fully failed turns, but it is a poor user experience for late upstream interruptions after the model has already produced useful text. The backend already tracks `full` content while streaming and can distinguish empty failures from late failures.

Structured PDF parsing is now observable per paper and can be manually rerun from paper detail. Stable use needs the same operation in the maintenance center so admins can refresh a bounded set after enabling Docling, a command parser, or a better mirror/cache state.

Similar systems:
- RAGFlow exposes parser choices and document processing state as operational controls for knowledge ingestion.
- paperless-ngx treats document processing and searchability as system-wide maintenance concerns, not just per-document actions.

## Goals / Non-Goals

**Goals:**
- Avoid appending late stream failure warnings to otherwise useful paper-chat answers.
- Preserve visible failure messaging for turns that produce no answer content.
- Expose structured parse batch maintenance through existing admin maintenance APIs and UI.
- Keep batch operations bounded and synchronous like existing maintenance actions.

**Non-Goals:**
- Add a background job queue or progress polling UI.
- Redesign the paper chat renderer.
- Add a new structured parse result table.

## Decisions

1. Introduce a paper-chat stream warning event for late failures.
   - Rationale: the frontend can mark the assistant turn as interrupted without adding warning prose to the answer content.
   - Alternative considered: always append a shorter warning. Rejected because it still pollutes saved chat history and copied answers.

2. Keep the existing error content path for empty turns.
   - Rationale: if no useful answer exists, visible failure text is the correct primary output.

3. Add `POST /papers/maintenance/backfill-structured-pdf`.
   - Rationale: it mirrors existing bounded maintenance actions for full text and embeddings while reusing `force_structured_pdf_reparse`.

4. Select papers by missing or failed structured parse status.
   - Rationale: maintenance should focus on papers that can improve reliability rather than reparsing every paper by default.

## Risks / Trade-offs

- [Risk] Synchronous batch parsing can take time. -> Keep a low bounded default and reuse frontend action loading state.
- [Risk] Late stream interruption may hide provider instability. -> Preserve a compact turn warning/status and backend logs.
- [Risk] Batch parse failures can be noisy. -> Return per-paper errors through existing `MaintenanceActionResult`.
