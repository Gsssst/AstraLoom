## Context

Paper-detail Q&A currently builds a current-paper context and streams plain SSE text. The main chat workspace already supports bounded related-paper retrieval, web enhancement, depth settings, JSON SSE events, progress states, and blank-response protection.

## Goals / Non-Goals

**Goals:**
- Align paper-detail configuration and stream behavior with main chat.
- Preserve the current paper as the core evidence source.
- Allow optional related-paper and web context augmentation.

**Non-Goals:**
- Replace paper-specific context with a generic chat session.
- Add file uploads to the paper-detail panel.
- Add a database schema migration.

## Decisions

- Treat current-paper context as mandatory and the paper-library toggle as additional related-paper retrieval.
- Reuse the existing chat-session retrieval helper and JSON SSE helper at request time to keep behavior aligned.
- Include related-paper references in stream metadata and persist them in personal paper-chat history.
- Use a buffered JSON SSE consumer in the paper detail page.

## Risks / Trade-offs

- [Risk] Runtime helper imports couple paper Q&A to shared chat behavior. → Import helpers inside request handling to avoid route-import cycles while keeping one retrieval strategy.
- [Risk] Additional retrieval can add latency. → Keep bounded depth limits and show progress text.
