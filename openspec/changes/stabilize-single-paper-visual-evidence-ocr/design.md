## Context

The visual evidence pipeline now OCRs every weak visual table by default and saves the results for later paper Q&A. That is the right evidence behavior, but the single-paper "提取视觉证据" endpoint still performs the full extraction inside the request handler. A paper with several weak table pages can therefore hit the browser/proxy request timeout even though the backend work is valid and should continue.

The maintenance backfill endpoint already uses a background job model. Single-paper extraction should follow the same interaction pattern instead of reducing OCR coverage.

## Goals / Non-Goals

**Goals:**

- Start single-paper visual evidence extraction quickly and return a pollable job id.
- Keep full weak-table OCR and persisted OCR results.
- Let the frontend report queued/running/success/failed states without waiting on a long request.
- Preserve existing `DocumentVisualEvidenceStatus` fields so current detail cards can still render.

**Non-Goals:**

- Add a new queueing dependency.
- Add a user-visible OCR configuration toggle.
- Reintroduce a low default OCR cap.

## Decisions

1. Reuse the existing in-memory maintenance job registry.
   - This keeps the change small and matches the existing "提取 5 篇视觉证据" background behavior.
   - A production queue can replace it later without changing frontend semantics.

2. Change single-paper extraction to enqueue background work and return immediately.
   - The response contains the current visual status and job metadata.
   - The job force-reparses visual evidence and commits results when complete.

3. Poll existing job/status endpoints from the frontend.
   - The frontend can poll `/papers/maintenance/jobs/{job_id}` and refresh paper records/status after completion.
   - If enqueue fails, the existing error alert path remains.

## Risks / Trade-offs

- [Risk] In-memory jobs are lost on process restart. -> Existing maintenance jobs already share this limitation; persisted extraction metadata remains the source of truth after successful completion.
- [Risk] Multiple clicks can enqueue duplicate work. -> Track job state by paper id and return the active job while it is queued/running.
- [Risk] OCR can still fail per model timeout. -> The job records failed status and the visual evidence status stores `last_error` for UI display.
