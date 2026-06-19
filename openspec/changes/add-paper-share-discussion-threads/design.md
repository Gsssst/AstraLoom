## Context

The app already supports paper chat sharing through `paper_chat_share` notifications. Those notifications carry enough metadata to display the paper title, sender, selected messages, source paper path, and recipient mode. The app also has a mature internal pattern for comments through workspace issue comments: a parent resource, ordered comments, user attribution, and in-app notifications for related users.

External references inform the interaction model:

- Hypothesis keeps discussion attached to a document selection or annotation, not as detached chat.
- giscus maps each page/topic to a discussion thread and supports comments/reactions around that thread.
- Novu-style notification centers treat notifications as actionable items with enough metadata to continue the workflow.

For this product, each shared paper AI insight should behave as a small thread attached to the share notification.

## Goals / Non-Goals

**Goals:**

- Make arbitrary-user paper chat shares discussable from the paper push center.
- Preserve share context: paper, sender, selected messages, recipients, source path.
- Support ordered comments with author identity and timestamps.
- Support per-user status labels: useful, follow-up needed, resolved.
- Notify sender and previous participants when a new comment is added.

**Non-Goals:**

- No real-time WebSocket updates in the first iteration.
- No threaded nested replies; comments are a flat chronological list.
- No rich editor, attachments, or @mentions.
- No project-space-only binding.

## Decisions

1. **Use a share-thread identifier stored in notification metadata.**

   A thread can span sender and multiple recipient notifications. On share creation, generate `share_thread_id` and store it in every related `paper_chat_share` notification. Older notifications without this id can fall back to their notification id as a private thread.

2. **Persist thread comments separately from notifications.**

   Notifications remain delivery records. Comments belong to the discussion thread so all participants can see the same conversation, regardless of which individual notification they opened.

3. **Persist per-user share status separately.**

   Status like useful/follow-up/resolved is personal workflow state. Keeping it separate avoids mutating shared thread content and lets different users triage the same share differently.

4. **Authorize by notification ownership or sender participation.**

   A user can access a share thread if they own a notification carrying that thread id, originally sent the share, or are a recorded participant. This supports arbitrary-user shares without requiring a project space.

5. **Render discussion only when a share card is expanded.**

   This preserves the scannable collapsed feed from the previous change while making collaboration available after intent is clear.

## Risks / Trade-offs

- [Risk] Existing share notifications do not have `share_thread_id`. -> Treat their notification id as a legacy single-notification thread and avoid breaking display.
- [Risk] Notification fan-out can become noisy. -> Notify sender and commenters except the actor, not every user in the system.
- [Risk] Users may expect live updates. -> Provide refresh-after-post and keep real-time updates for a later phase.
