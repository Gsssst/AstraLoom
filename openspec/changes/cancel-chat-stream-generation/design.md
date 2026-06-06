## Context

The chat page uses `fetch()` to POST to `/chat-sessions/{id}/send-stream` and then reads the response body with a stream reader. There is currently no way for the user to stop an in-flight stream once it starts.

Comparable chat applications expose a stop-generation control during streamed responses. For this app, a browser-side cancellation is enough for the first iteration because the request is owned by the current page and FastAPI streaming responses stop producing data once the client disconnects.

## Goals / Non-Goals

**Goals:**
- Show a stop button while `sending` is true.
- Abort the active stream request immediately.
- Avoid showing cancellation as an error toast.
- Keep partial streamed content visible.
- Reset local sending and timing state so the user can send again.

**Non-Goals:**
- Add a server-side job cancellation endpoint.
- Delete partially streamed messages.
- Cancel background retrieval jobs outside the active request lifecycle.

## Decisions

- Store the active `AbortController` in a React ref.
  - Rationale: the controller should survive renders without causing rerenders and can be cleared in `finally`.

- Pass the controller signal to both normal and attachment stream fetches.
  - Rationale: both send paths use the same stream endpoint and need the same cancellation semantics.

- Detect `AbortError` and suppress the generic assistant error message.
  - Rationale: user-initiated cancellation is expected behavior, not a failed model call.

- Mark streaming assistant messages as no longer streaming after cancellation.
  - Rationale: partial content should become stable and action buttons should work again.

## Risks / Trade-offs

- If the server has already completed and persisted the reply, cancellation may not prevent persistence -> mitigation: the UI only promises to stop the current browser stream, not rewind server-side state.
- Some browsers report abort errors differently -> mitigation: check both `name === "AbortError"` and the ref flag.
