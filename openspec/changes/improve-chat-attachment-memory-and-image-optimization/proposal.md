## Why

Temporary PDF/image attachments now work for the current question, but follow-up questions can lose the uploaded context unless users reattach the same file. Large images are also accepted up to 50MB but are sent as full data URLs, which can make requests slow, expensive, or rejected by upstream vision models.

## What Changes

- Keep extracted temporary attachment context available for follow-up turns in the same chat surface until the user removes or clears it.
- Show remembered attachment chips separately from current-turn attachment chips.
- Compress large image attachments before they are sent to the model while preserving the original 50MB upload acceptance limit.
- Surface clear attachment optimization status so users understand when images were reduced for model input.

## Capabilities

### New Capabilities
- `chat-attachment-session-memory`: Chat surfaces can retain temporary attachment context across follow-up questions.
- `chat-image-send-optimization`: Chat surfaces optimize uploaded image payloads before model submission.

### Modified Capabilities
- None.

## Impact

- Affects shared chat attachment frontend state, main chat request construction, paper-detail chat request construction, and attachment UI.
- No new database tables, paper-library ingestion behavior, or backend upload endpoints are required.
- Adds frontend contract coverage for remembered attachments and optimized image payload metadata.
