## Context

`PaperDigestInboxPage` is labeled "论文推送中心" and calls `/notifications/digests`, but the backend filters that route to `category == "digest"`. Paper chat shares use `category == "paper_chat_share"`, so they only appear in the global notification popover. The user-facing naming makes this feel like missing data.

## Goals / Non-Goals

**Goals:**

- Treat daily digests and paper chat shares as paper push center items.
- Preserve all daily digest interactions: ingest, reading queue, feedback.
- Add a paper chat share card that shows selected question/answer excerpts and opens the source paper.
- Make unread count and "全部标记已读" cover both `digest` and `paper_chat_share`.

**Non-Goals:**

- No new notification category.
- No separate database table or migration.
- No editing/replying to shared excerpts in this slice.

## Decisions

1. **Reuse `/notifications/digests` as the paper push feed.**

   This is the existing route used by the page. Expanding its category filter keeps frontend routing stable and matches the page title.

2. **Branch render by category on the page.**

   Daily digest notifications continue using `metadata.papers`. Paper chat share notifications use `metadata.selected_messages`, `sender_name`, `paper_title`, `note`, and `path`.

3. **Keep feedback endpoints digest-only.**

   Paper chat shares do not contain recommended paper rows, so paper feedback remains limited to category `digest`.

## Risks / Trade-offs

- [Risk] The route name `/digests` is now broader than pure daily digests. -> The page already uses "论文推送中心"; this is acceptable for compatibility.
- [Risk] The count label "次摘要" becomes inaccurate. -> Update UI copy to count "条推送" and distinguish daily digest vs精读分享 tags.
