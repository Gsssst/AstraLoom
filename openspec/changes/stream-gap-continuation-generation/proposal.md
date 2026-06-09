## Why

Continuing proposal generation from an existing Gap Map can exceed the frontend's 30-second axios timeout because it runs the full candidate generation, review, novelty, and selection pipeline synchronously. The initial generation path already avoids this by using SSE progress streaming, so the continuation path should use the same long-running request pattern.

## What Changes

- Add a streaming continuation endpoint for `continue-from-gaps` that emits run, stage, artifact, done, cancelled, and error events.
- Update the frontend Gap Map continuation action to consume the streaming endpoint instead of a regular axios request.
- Preserve the existing non-streaming continuation endpoint for compatibility.
- Keep cancellation behavior consistent with current generation cancellation.

## Capabilities

### New Capabilities

### Modified Capabilities

- `research-idea-workbench`: Gap Map continuation SHALL support long-running streaming generation so proposal generation does not fail solely because of the default frontend request timeout.

## Impact

- Backend API: `backend/app/api/research.py`.
- Frontend page: `frontend/src/pages/ResearchProjectPage.tsx`.
- Contract/regression tests for generation control and Gap Map selection.
- No database schema changes and no new external dependencies.
