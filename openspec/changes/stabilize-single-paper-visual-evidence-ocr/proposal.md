## Why

Single-paper visual evidence extraction now performs full weak-table OCR, which can exceed an interactive HTTP request timeout when a paper has many table pages or a slow model call. The user should be able to start extraction without losing the job, and the system should keep saving OCR results in the background.

## What Changes

- Make single-paper visual evidence extraction enqueue a background job instead of synchronously waiting for the whole OCR run.
- Return the current visual evidence status plus a pollable job id/status when extraction is queued.
- Keep the full weak-table OCR behavior; do not reduce OCR coverage to avoid timeouts.
- Surface timeout/failure details through the existing visual evidence status/job status path.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `document-visual-evidence-pipeline`: Single-paper extraction must run as non-blocking background work when OCR can be long-running.
- `paper-library-maintenance-center`: Paper library actions must expose pollable progress/failure state for single-paper visual evidence extraction.

## Impact

- Backend API: `/papers/{paper_id}/extract-visual-evidence` response shape may include queued job metadata while preserving visual evidence status fields.
- Backend services: add/reuse an in-memory job runner for single-paper visual evidence extraction.
- Frontend: trigger extraction, show queued/running status, and poll the job/status instead of treating request timeout as terminal failure.
- Tests: add API/UI-contract regressions for queued extraction and timeout-safe behavior.
