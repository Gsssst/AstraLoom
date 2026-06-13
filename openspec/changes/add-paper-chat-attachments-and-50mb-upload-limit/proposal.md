## Why

Paper-detail AI Q&A lacks the same temporary PDF/image attachment workflow that the main chat already provides, so users cannot ask about an extra PDF or figure while staying in the paper reader. The current main chat attachment limit is also too small for many research PDFs and should be raised from 10MB to 50MB.

## What Changes

- Raise temporary chat attachment size validation from 10MB to 50MB.
- Add PDF/image attachment controls to paper-detail AI Q&A.
- Reuse the existing attachment extraction endpoint so PDFs contribute extracted text and images contribute model-ready data URLs.
- Include paper-detail attachments in the displayed user message and request context without importing them into the paper library.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `chat-workspace-visual-refinement`: chat attachments accept PDF/image files up to 50MB.
- `paper-detail-chat-parity`: paper-detail AI Q&A supports temporary PDF/image attachments in addition to current-paper context.

## Impact

- Affects frontend chat attachment state, upload UI, and paper-detail ask request construction.
- Reuses existing `/chat-sessions/extract-file`; no backend endpoint, database, or dependency changes are expected.
- Adds frontend contract coverage for 50MB validation and paper-detail attachment UI/context.
