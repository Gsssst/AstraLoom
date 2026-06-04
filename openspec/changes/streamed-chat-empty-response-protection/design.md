## Context

The streamed LLM wrapper only yields `delta.content`. A reasoning model can emit `reasoning_content` without final answer text when its output budget is exhausted. The session endpoint then saves an empty assistant message. Separately, the frontend parses each received byte chunk independently, even though SSE frames can cross chunk boundaries.

## Goals / Non-Goals

**Goals:**
- Retry reasoning-only or otherwise empty LLM streams once.
- Persist a visible fallback instead of an empty assistant reply.
- Preserve multiline and chunk-split streamed content.
- Give the user visible progress feedback during longer requests.

**Non-Goals:**
- Stream the model's private reasoning text.
- Change non-session streaming endpoints in this focused repair.

## Decisions

- Retry an empty stream once, raising the token budget to 8192 when reasoning output was observed.
- Encode session stream payloads as JSON objects with `content`, `status`, `error`, and `done` event types.
- Use a buffered frontend consumer shared by text and attachment requests.
- Persist a short fallback message when the model still returns no visible content after retry.

## Risks / Trade-offs

- [Risk] A retry can increase latency for rare empty responses. → Show progress text and retry only once.
- [Risk] Session SSE format changes. → Update the only session-stream frontend consumer in the same change and preserve focused backend tests.
