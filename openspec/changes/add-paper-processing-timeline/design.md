## Context

The automated paper-processing pipeline already records summary readiness labels plus pipeline metadata such as `last_checked_at`, `last_completed_at`, `queued_steps`, `running_steps`, `failed_steps`, and `last_error`. The missing layer is a user-facing per-paper timeline that explains what each artifact step is doing and when it last changed.

## Goals / Non-Goals

**Goals:**

- Derive a compact timeline for each local paper from the existing processing snapshot and metadata.
- Expose the timeline through the existing paper detail/status APIs.
- Show the timeline on the paper detail page without making the maintenance center the normal workflow.
- Preserve failure reasons and automation retry hints so users can distinguish pending work from stuck or failed work.

**Non-Goals:**

- Add a new job table or durable workflow engine.
- Change the processing order, OCR strategy, parser behavior, embedding model, or BM25 implementation.
- Add manual queue controls to the paper detail page.
- Reprocess existing papers solely to populate timeline history.

## Decisions

1. Derive timeline items from `PaperProcessingSnapshot.labels` and `paper_processing_pipeline` metadata.
   - Rationale: Labels already encode readiness and action state, while metadata records running/queued/failed/global timestamps. A derived view avoids divergent state.
   - Alternative considered: create a separate timeline table. Rejected because current metadata is sufficient for the first user-visible timeline and a new table would require migrations and backfill.

2. Add a serializable timeline helper in the processing service.
   - Rationale: Keeping derivation close to snapshot logic makes API endpoints and tests share the same state semantics.
   - Alternative considered: derive timeline entirely in the frontend. Rejected because failure metadata and retry hints are backend-owned and should stay consistent across API clients.

3. Expose the timeline in paper detail and processing-status payloads.
   - Rationale: The paper detail page can render immediately from the existing fetch, while the status endpoint remains useful for diagnostics and tests.

4. Use coarse timestamps when per-step completion history is unavailable.
   - Rationale: Existing metadata has global `last_completed_at`, not per-step completion times. Ready steps can show the global completion/check time with clear wording rather than fabricating exact per-step history.

## Risks / Trade-offs

- [Risk] Timeline is not a full historical audit log. -> Mitigation: label it as current processing timeline/status and only show timestamps that exist.
- [Risk] Some old papers have no pipeline metadata. -> Mitigation: derive useful ready/pending states from artifact labels and omit missing timestamps.
- [Risk] Failed-step metadata shape may vary. -> Mitigation: normalize string and object forms defensively in the helper.
