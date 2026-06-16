## Why

During streaming answers, the chat view still snaps back to the bottom when the user scrolls upward to read already generated content. This breaks the expected review-while-generating workflow and regresses the prior manual-scroll-aware behavior.

## What Changes

- Harden the shared chat auto-scroll hook so manual upward scrolling pauses follow-output during active streams.
- Resume follow-output only when the user returns near the bottom or sends a new message.
- Attach explicit scroll handlers to chat containers so wheel/touch/trackpad gaps do not miss manual-scroll intent.
- Extend contract tests to cover the stronger manual scroll lock behavior.

## Capabilities

### New Capabilities

### Modified Capabilities
- `chat-composer-bottom-alignment`: Chat streaming must preserve the user's manual scroll position instead of forcing bottom follow.

## Impact

- Frontend shared hook `frontend/src/hooks/useChatAutoScroll.ts`.
- Main chat page and paper detail chat scroll containers.
- Frontend contract tests for chat auto-scroll behavior.
