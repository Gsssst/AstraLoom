## Context

The main chat page and paper-detail AI Q&A both call `scrollIntoView({ behavior: 'smooth' })` whenever streamed content updates. During a long answer this produces a continuous forced scroll to the bottom, so users cannot scroll upward to inspect earlier parts of the answer while generation continues.

## Goals / Non-Goals

**Goals:**
- Keep bottom-following behavior when the user is already reading the latest output.
- Stop forcing the message list to the bottom after the user manually scrolls away from the bottom.
- Re-enable bottom-following when the user scrolls back near the bottom.
- Share the behavior between main chat and paper-detail chat.

**Non-Goals:**
- Changing stream transport, message persistence, retrieval, or answer formatting.
- Adding a new visible state unless it becomes necessary for usability.

## Decisions

- Add a small React hook for streaming chat scroll state.
  - The hook owns the scroll container ref, the bottom sentinel ref, and a `followOutputRef`.
  - Scroll listeners update `followOutputRef` based on whether the user is within a small threshold of the bottom.
- Replace unconditional `scrollIntoView` effects with conditional bottom-following.
  - New content scrolls to bottom only when `followOutputRef` is true.
  - User scrolls away from the bottom flip it to false, so subsequent stream chunks do not fight the user.
- Use instant or auto scrolling for token updates rather than smooth scrolling on every chunk.
  - Smooth scrolling is suitable for one-off navigation, but repeated smooth calls during streaming can stack animations and feel uncontrollable.

## Risks / Trade-offs

- [Risk] The threshold is too small and auto-follow disables unexpectedly near the bottom. → Use a tolerant 48px threshold and centralize it in the hook.
- [Risk] Existing initial-load behavior no longer lands at the newest message. → The hook starts in follow mode and remains in follow mode while the user stays near the bottom.
