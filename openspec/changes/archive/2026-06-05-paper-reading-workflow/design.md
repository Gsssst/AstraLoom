# Design: Paper Reading Workflow

## Overview

The workflow turns `UserPaper.read_status` into a visible, actionable reading queue. The backend exposes status counts, while the frontend shows a segmented queue filter and quick status actions on paper cards. The detail page mirrors the same status control so users can update progress while reading or chatting with a paper.

## Backend

### Status Counts

Add `GET /api/papers/collection/reading-status-counts`, returning:

```json
{
  "unread": 2,
  "reading": 4,
  "completed": 7
}
```

The endpoint counts rows in `user_papers` for the current user grouped by `read_status`. Missing statuses return `0`.

### Reading List

Keep `GET /api/papers/collection/reading-list?status=...`, but validate the status against `unread|reading|completed` and return each paper with an optional `read_status` field.

### Status Update

Keep `PUT /api/papers/{paper_id}/read-status`, and return both:

```json
{
  "read_status": "reading",
  "saved": true
}
```

This confirms that moving a paper into the reading workflow also makes it part of the user's personal paper state.

## Frontend

### Paper Library

When `source === "reading"`:

- Show three compact status chips:
  - `待读`
  - `阅读中`
  - `已完成`
- Display counts from `/collection/reading-status-counts`.
- Query `/collection/reading-list` with the selected status.
- Show quick actions on cards:
  - `开始阅读`
  - `标记完成`
  - `重置待读`

After a status update, refresh counts and remove the card from the current filtered list if it no longer belongs there.

### Paper Detail

Load `read_status` from `/papers/{paper_id}/user-state`, show a compact control in the toolbar, and persist updates with `/read-status`.

## Compatibility

No schema changes. Existing saved papers, notes, and chat history remain untouched. Updating read status creates or updates the current user's `UserPaper` row, matching existing backend behavior.
