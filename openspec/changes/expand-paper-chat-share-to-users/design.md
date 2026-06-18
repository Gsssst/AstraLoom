## Context

The previous paper-chat collaboration share flow sends one assistant answer to members of a project space linked to the paper. That is too narrow for day-to-day research collaboration: a user may want to send a useful exchange to a collaborator who is not in the paper's project space, and often the useful context is not one answer but a small sequence of user questions and assistant replies.

Before designing this slice, mature collaboration products were reviewed at the repository/product level:

- Zulip is an open-source team chat application focused on productive team conversations.
- Mattermost is an open-source, self-hosted collaboration platform implemented with React, Go, and PostgreSQL.
- Element Web is a Matrix web client for collaboration.

The useful shared pattern across these products is not "copy one message into another feature"; it is "select a conversation unit, choose recipients, preserve source context, and notify recipients with a way back to the original place." This change applies that pattern to paper reading conversations.

## Goals / Non-Goals

**Goals:**

- Allow an authenticated user to search active users and choose recipients for a paper-chat share.
- Allow the sender to select multiple user/assistant messages from the current paper conversation.
- Store role, content, display content, evidence references, and index metadata for each selected message with strict bounds.
- Send each recipient a `paper_chat_share` notification with paper metadata, sender metadata, selected messages, optional note, and source path.
- Keep the old single-answer shortcut usable by mapping it to the new multi-message payload.

**Non-Goals:**

- No public links, external messaging, email delivery, or websocket delivery.
- No full chat-history sharing by default; the sender must explicitly select messages.
- No recipient-side threaded discussion in this slice.
- No project-space activity is required for direct-user shares, because there may be no project-space target.

## Decisions

1. **Direct user recipients are primary.**

   The share request accepts `recipient_user_ids`. The backend validates that every recipient exists, is active, and is not the sender. This avoids leaking messages to deleted/inactive accounts and avoids self-notification noise.

2. **Selected messages are sent as a bounded JSON bundle.**

   The API accepts `selected_messages` with role, content, optional display content, message index, and references. The backend limits message count and text/reference sizes before storing notification metadata. This reuses `Notification.metadata_json` and avoids a migration.

3. **The existing workspace share shape remains a compatibility path.**

   If an old client submits `space_id`, `question`, and `answer`, the backend can still create workspace notifications. New clients send selected messages and direct recipients. This lowers deployment risk when frontend and backend are not restarted at the exact same time.

4. **Frontend adds selection mode rather than always showing checkboxes.**

   Paper chat stays readable by default. A "选择推送" mode shows checkboxes on messages, a selected count, and a button to open the share modal. The assistant-card shortcut preselects the adjacent question/answer pair.

5. **Recipient search is paper-scoped API surface, but user-backed.**

   Add `GET /api/papers/{paper_id}/share-recipients?q=&limit=` so the paper detail page can fetch candidates without depending on workspace owner APIs. The route still verifies the paper exists and requires authentication.

## Risks / Trade-offs

- [Risk] Notification metadata can become large. -> Bound selected messages, text, and references, and store excerpts in top-level metadata.
- [Risk] Users may accidentally share too much context. -> Require manual selection and show a preview before sending.
- [Risk] Search exposes user emails to all authenticated users. -> Return only active users and keep this aligned with existing member-candidate behavior; a future privacy setting can hide email if needed.
- [Risk] Old workspace behavior and new direct-user behavior diverge. -> Keep shared helper functions for bounds and metadata shape.

## Migration Plan

- Deploy backend first: old and new payloads should both be accepted.
- Deploy frontend second: new UI uses direct recipients and selected messages.
- Rollback frontend safely: old `space_id` path remains available.
