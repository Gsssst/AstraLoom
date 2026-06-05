## Context

Paper-detail Q&A uses the shared model streaming service, but it has a larger prompt because it combines current-paper chunks with optional related-paper and network context. A reasoning-heavy model response can therefore exhaust its visible-answer budget and fall through to the generic warning. Both chat surfaces currently keep reasoning text in one page-level state, so completed turns are not associated with their own reasoning panel.

## Goals / Non-Goals

**Goals:**
- Recover a visible paper answer before displaying the final empty-response warning.
- Attach reasoning text and completion state to the assistant message for the corresponding turn.
- Let authenticated users clear saved paper-chat history while preserving notes and collection state.

**Non-Goals:**
- Persisting main-chat reasoning in the relational chat-message schema.
- Adding paper-chat sessions or changing the existing paper collection data model.
- Removing the final warning when both primary generation and recovery fail.

## Decisions

- Add a paper-specific stream helper that first uses the requested mode, then retries an empty primary stream with a concise-answer system instruction and the stable content stream.
- Emit a status event when recovery begins so the UI explains the additional wait.
- Store reasoning fields inside each frontend assistant message. Paper history can persist these fields because it is already stored as JSON; main-chat reasoning remains available for the current page session without a database migration.
- Add a dedicated `DELETE /papers/{paper_id}/chat-history` endpoint that resets only `paper_chat_history`, preserving the `UserPaper` row and its other personal fields.

## Risks / Trade-offs

- [Risk] Recovery adds latency after an empty primary stream. → Mitigation: run recovery only when no visible content was emitted and expose a clear status message.
- [Risk] Previously saved paper history has no reasoning fields. → Mitigation: treat reasoning fields as optional.
- [Risk] Clearing Q&A history could remove useful context accidentally. → Mitigation: require an explicit confirmation in the frontend.
