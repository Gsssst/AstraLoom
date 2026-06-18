## Context

The direct-user paper chat share flow stores `selected_messages`, sender, paper metadata, note, and source path in `Notification.metadata_json`. The global notification popover currently discards most of that structure and displays only a one-line description. This makes the feature feel like a link notification rather than a useful collaboration artifact.

Mature collaboration tools such as Zulip, Mattermost, and Element Web keep enough message context in notification/inbox surfaces for users to triage work without leaving the current page, while still preserving a route back to the original conversation or document. This change applies that pattern to paper AI reading shares.

## Goals / Non-Goals

**Goals:**

- Render selected paper chat messages directly in the notification popover for `paper_chat_share`.
- Preserve the current ability to click through to `/papers/<paper_id>`.
- Let senders choose all active users with one action from the share modal.
- Let backend broadcast to all active users except the sender via an explicit `all_users` flag.

**Non-Goals:**

- No separate full-screen notification center page.
- No replies/comments inside notifications.
- No external push/email delivery.
- No role-based broadcast policy in this slice; any authenticated sender can use the same active-user set exposed by recipient search.

## Decisions

1. **Render a specialized card for `paper_chat_share`.**

   The popover keeps the existing list structure, but the description for this category renders metadata: note, selected messages, paper title, and action button. This keeps the change local to `AppLayout`.

2. **Use explicit buttons to avoid accidental navigation.**

   Clicking the action button opens the source paper. The card can still mark as read when opened, but previewing content should not immediately force navigation.

3. **Add `all_users` to the existing share endpoint.**

   The frontend can still use `recipient_user_ids` for selected recipients. For broadcast, it sends `all_users: true`; the backend resolves all active non-sender users and reuses the same notification creation path.

4. **One-click all users selects currently loaded candidates and marks broadcast mode.**

   The modal button is visible as "推送所有用户". It sets `allUsers` in frontend state and fills visible recipient ids for transparency. Submit sends `all_users: true`.

## Risks / Trade-offs

- [Risk] Broadcast can create many notifications. -> Bound the same content payload and exclude the sender; future policy can restrict this to admin if needed.
- [Risk] Notification popover can become too tall. -> Limit displayed messages and use ellipsis/scrolling in the card.
- [Risk] Users confuse preview and source paper navigation. -> Provide an explicit "打开论文" action.
