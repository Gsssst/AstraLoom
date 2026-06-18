## Context

Current paper AI Q&A is personal: messages are saved in `UserPaper.paper_chat_history` and only the current user sees the useful reading exchange. Project spaces already provide the correct collaboration boundary through members, linked resources, activity logs, and in-app notifications.

Before implementation, mature collaboration products were reviewed for patterns:

- Zotero group libraries: use a shared collection boundary with member permissions for research artifacts.
- Hypothesis private groups: share annotation-like units with source context rather than entire private reading sessions.
- Mattermost-style team collaboration: use actionable notifications and a lightweight activity feed to bring members back to the relevant work.
- Outline-style knowledge bases: turn discussion into durable project knowledge entries rather than ephemeral messages.

The project already has the primitives needed for the MVP:

- `ProjectSpace`, `ProjectSpaceMember`, and `ProjectSpaceResource` define which paper belongs to which member group.
- `ProjectSpaceActivity` records durable collaboration events.
- `Notification` powers the global header unread badge and popover.
- `PaperDetailPage` already has assistant messages with question, answer, evidence references, and paper metadata.

## Goals / Non-Goals

**Goals:**

- Let a user select a useful paper AI answer and push it to members of a linked project space.
- Preserve enough context for recipients: paper title/id, original user question, AI answer excerpt/full content, evidence references, sender, workspace, and source path.
- Enforce workspace membership and paper linkage so personal reading notes are not leaked to unrelated users.
- Reuse notification and workspace activity infrastructure without adding a new persistence table.
- Add tests that lock the backend permission contract and frontend share affordance.

**Non-Goals:**

- No real-time chat, websocket channel, or threaded comment system in this MVP.
- No cross-workspace sharing or public links.
- No automatic sharing of full paper chat history.
- No email, Feishu, or external messaging delivery.
- No AI-generated social summary beyond the selected answer content.

## Decisions

1. **Use project spaces as the share target.**

   A paper chat answer can only be shared to spaces where the current user is a member and the paper is linked as a `papers` resource. This mirrors the shared-library/private-group pattern and avoids creating a second permission model.

2. **Represent the shared insight as notifications plus workspace activity.**

   Each recipient gets a `Notification` with category `paper_chat_share`. The workspace receives one `ProjectSpaceActivity` item with action `paper_chat_shared`. This avoids schema migration while still giving recipients an inbox item and the workspace a durable trail.

3. **Create a narrow paper API endpoint.**

   Add:

   - `GET /api/papers/{paper_id}/share-targets`: returns linked spaces visible to the current user.
   - `POST /api/papers/{paper_id}/share-chat-insight`: validates membership/linkage, stores activity, and creates notifications for other members.

   Keeping this under papers makes the frontend integration simple and keeps the payload paper-specific.

4. **Frontend share entry lives on assistant answer cards.**

   Assistant messages get a compact "推送成员" action next to copy/regenerate. A modal lets the user choose a linked workspace and optionally edit a short note. If no linked workspace exists, the modal explains that the paper must be linked to a project space first.

5. **Notification routing uses metadata path first.**

   The notification metadata includes `path: /papers/<paper_id>?share=<notification_id>`. The existing global notification popover can navigate via metadata path; it only needs the new category label/color.

## Risks / Trade-offs

- [Risk] Notifications duplicate large AI answers for every recipient. -> Mitigation: bound answer/question/note/reference payload sizes in the API and store only a curated card, not entire chat history.
- [Risk] A user may share low-quality AI output. -> Mitigation: require an explicit user action and optional note, and preserve evidence references so recipients can inspect the source.
- [Risk] Users expect comments or replies immediately. -> Mitigation: the MVP routes back to the paper and records an activity item; comments/threading are listed as a follow-up collaboration feature.
- [Risk] Existing global notification UI becomes noisy. -> Mitigation: use a distinct category and concise content; future work can add a dedicated collaboration feed filter.

## Future Collaboration Ideas

- Shared reading tasks: assign a paper/question to a member with due date and status.
- Inline comments on shared AI insight cards.
- @mentions in workspace issues and shared insights.
- Weekly workspace reading digest from shared insights, annotations, and completed papers.
- Team reading progress board with "who read what" and unresolved questions.
- Voting or reaction tags for "important", "needs verification", and "follow-up experiment".
