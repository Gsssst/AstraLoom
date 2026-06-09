## Context

Initial proposal generation uses `/idea-runs/stream` and pushes progress through SSE. Gap Map continuation currently uses a standard axios POST to `/continue-from-gaps`, but that server call performs the same heavy work and can exceed the global 30-second axios timeout. The fix should align continuation with the existing streaming pattern rather than globally increasing timeouts.

## Goals / Non-Goals

**Goals:**

- Make Gap Map continuation resilient to long-running model and scholarly-search steps.
- Reuse existing run progress events and cancellation behavior.
- Keep the existing synchronous endpoint available for tests and external callers.

**Non-Goals:**

- Change the research idea algorithm.
- Add background workers or queue persistence.
- Add new UI panels or change the Gap Map selection model.

## Decisions

- Add `/continue-from-gaps/stream` instead of changing the existing endpoint.
  - Rationale: existing callers remain compatible, and the frontend can opt into streaming for user-triggered long tasks.
- Extract a small SSE runner helper for idea-run execution.
  - Rationale: initial generation and continuation need identical queue, cancellation, and event formatting behavior.
- Use `fetch` with `AbortController` in the frontend continuation flow.
  - Rationale: it mirrors initial generation and bypasses the axios 30-second timeout.

## Risks / Trade-offs

- Browser disconnect cancels the run -> this matches current streaming generation behavior.
- A failed backend task may still emit a final `done` event with failed run status -> frontend already handles failed run status after stream completion.
- Two endpoints now support continuation -> document the streaming endpoint through code tests and keep the old endpoint for compatibility.
