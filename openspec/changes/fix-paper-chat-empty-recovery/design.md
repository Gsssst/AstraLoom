## Context

The paper chat streaming path currently has two stages:

1. Primary stream, optionally with thinking events.
2. Recovery stream with a stricter prompt if the primary stream emits no visible content.

If the recovery stream also emits no content, the outer `ask-stream` generator falls through to `EMPTY_STREAM_FALLBACK`, which is the warning visible in the UI. The user receives no answer even though the non-streaming `/ask` path may still be capable of returning one.

## Design

Add a third fallback inside `_stream_paper_answer_events`:

- Track whether recovery streaming emits any content.
- If recovery streaming returns no content or raises before content, call `llm_service.chat()` with the same recovery context.
- If non-streaming fallback returns text, emit it as a normal `content` event.
- If non-streaming fallback also returns empty or raises, let the outer stream produce the existing empty-response warning.

This keeps the stream event contract stable: callers still receive `status`, `meta`, zero or more `reasoning`/`content`/`warning`, then `done`.

## Non-Goals

- Do not change retrieval or evidence selection.
- Do not alter frontend rendering.
- Do not remove thinking display.

## Testing

- Unit test that primary and recovery streams empty, then non-streaming fallback returns content.
- Unit test that all fallbacks empty still produces the existing user-facing empty warning.
- Run focused paper chat tests.
