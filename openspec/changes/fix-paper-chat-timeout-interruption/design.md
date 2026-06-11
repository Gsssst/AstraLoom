## Context

The previous paper-chat reliability change correctly separated late interruption warnings from answer content. However, the warning is still triggered too often because `_stream_paper_answer_events()` wraps the entire `llm_service.chat_stream_with_thinking()` iterator in `asyncio.timeout(PAPER_CHAT_PRIMARY_TIMEOUT_SECONDS)`.

That timeout was intended to protect against reasoning-only or stalled streams, but it currently also limits healthy long answers. If visible content has already started and the answer takes more than 30 seconds, the server raises `TimeoutError`, treats it as a late interruption, and sends a warning.

## Goals / Non-Goals

**Goals:**
- Stop self-interrupting long, healthy paper-detail answers in thinking mode.
- Preserve fast recovery when a primary stream emits reasoning but no visible content.
- Preserve warning behavior for genuine provider/network failures after content has been emitted.
- Keep frontend behavior and SSE event names unchanged.

**Non-Goals:**
- Add a background job queue for paper Q&A.
- Change model selection or token budgets.
- Remove the existing compact interruption warning entirely.

## Decisions

1. Apply the timeout only while waiting for first visible content.
   - Rationale: after visible content starts, the user is receiving value and long paper answers should be allowed to finish.
   - Alternative considered: simply increase the timeout. Rejected because any fixed total timeout can still cut off valid long answers.

2. Treat reasoning-only timeout as recoverable, not as a late interruption.
   - Rationale: if no visible content exists, the existing stable recovery stream is the right product behavior.

3. Keep late exception handling unchanged once visible content exists.
   - Rationale: genuine upstream disconnects still need a compact "possibly incomplete" marker.

## Risks / Trade-offs

- [Risk] A provider can stream content very slowly for a long time. -> Mitigation: this preserves current request lifecycle behavior and avoids inventing new cancellation/progress controls in this narrow fix.
- [Risk] Reasoning may stream indefinitely before content. -> Mitigation: the first-visible-content guard still bounds that state and triggers recovery.
