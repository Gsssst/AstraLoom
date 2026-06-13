## Why

Paper processing is now automated, but users can only see coarse ready/pending labels. When a paper stays pending or fails, they cannot tell which artifact is queued, running, stale, failed, or already completed without returning to maintenance diagnostics.

## What Changes

- Add a per-paper processing timeline covering PDF availability, full text, structured parse, visual evidence/OCR, embeddings, and BM25/search readiness.
- Include step state, short detail, counts where available, relevant timestamps, failure reason, and a retry/automation hint in the timeline API payload.
- Show the timeline in the paper detail page as compact per-step status history near the existing readiness labels.
- Preserve the automatic background pipeline and avoid reintroducing a primary maintenance-center workflow for normal users.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `paper-library-maintenance-center`: paper processing status SHALL expose and render a per-paper timeline, not only summary labels.

## Impact

- Backend processing snapshot/status helpers and paper API response models.
- Paper detail frontend types and rendering.
- Backend tests for timeline serialization and failure metadata.
- Frontend contract coverage for the timeline UI.
