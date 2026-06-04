# Design: Paper Annotation and Reading Loop

## Backend

### Data Model

Add `UserPaper.personal_annotations` as a nullable JSON column. It stores a list of annotation objects:

```json
{
  "id": "uuid",
  "text": "selected PDF text",
  "page": 3,
  "kind": "quote",
  "note": "",
  "created_at": "2026-06-03T10:00:00Z"
}
```

This keeps annotations personal and avoids creating a global paper annotation table while the UX is still evolving.

### API

Add endpoints:

- `GET /api/papers/{paper_id}/annotations`
- `POST /api/papers/{paper_id}/annotations`
- `DELETE /api/papers/{paper_id}/annotations/{annotation_id}`

Creating an annotation creates a `UserPaper` row when missing and marks the paper as saved, matching existing note/chat behavior.

### Digest Reading Loop

Keep existing personal ingestion endpoint. On the frontend, after ingesting a digest paper, call `PUT /api/papers/{paper_id}/read-status` to place it in `unread` or `reading`.

If the ingest endpoint returns an existing paper id, it can be used directly. If a paper was already ingested during the current UI session, the page stores the returned id locally for future reading-status updates.

## Frontend

### Paper Detail

- Load annotations alongside user state and chat history.
- When PDF text is selected, keep the existing quote-to-chat behavior and also show the pending quote card.
- Add a "保存摘录" action on the pending quote card.
- Add an "摘录与引用" card in the content panel that lists saved annotations.
- Each annotation supports:
  - Ask AI with this quote
  - Delete

### Digest Center

- Update `handleIngest` to return the local paper id.
- Add action buttons:
  - `加入待读`
  - `开始阅读`
- Update "稍后阅读" feedback to ingest and mark the paper `unread`.
- Show the local loop state in tags so users know which recommendations already entered the queue.

## Verification

- Backend tests for annotation lifecycle and state preservation.
- Frontend production build.
- Layout contract tests.
- Strict OpenSpec validation.
- Browser verification attempted where available.
