## Context

Digest notifications are currently rendered inside the shared header popover. The popover is intentionally compact and truncates content, while digest metadata stores only a small subset of fetched papers. The existing paper library already supports remote arXiv preview ingestion through `/papers/ingest-personal`, so the new workflow can reuse the established deduplication and personal-save path.

## Goals / Non-Goals

**Goals:**
- Provide a readable digest history page under the paper library.
- Preserve compact header alerts while making digest alerts navigate to the inbox.
- Store enough structured arXiv metadata for paper cards and per-paper ingestion.
- Reuse the existing personal ingestion service and unread notification state.
- Keep older, sparse digest records usable.

**Non-Goals:**
- Add a new digest database table or migrate historical notifications.
- Implement bulk ingestion, email delivery, or recommendation feedback scoring.
- Replace the existing paper-library search experience.

## Decisions

### Use digest-category notifications as the inbox source

The inbox will query a category-specific notification endpoint rather than introduce a second persistence model. Digest content, creation time, unread state, and metadata already belong to `Notification`. This keeps scheduled and manual pushes visible in the same history and avoids schema migration.

Alternative considered: create a `paper_digests` table. This adds migration and synchronization cost without a current need for independent digest lifecycle fields.

### Store structured recommendation metadata in new notifications

New notifications will preserve each fetched paper's title, arXiv identifier, authors, year, and abstract snippet. Historical notifications remain compatible because the frontend treats missing fields as optional.

Alternative considered: refetch all metadata every time the inbox opens. That increases latency and makes historical digests dependent on remote arXiv availability.

### Reuse personal ingestion

Each recommendation card will call `/papers/ingest-personal` with `source=arxiv` and the arXiv identifier. The existing ingestion service handles remote resolution, deduplication, global paper creation, and personal library save behavior.

Alternative considered: add a digest-specific ingestion endpoint. That would duplicate existing authorization and persistence behavior.

### Treat the header popover as navigation

Clicking a digest notification marks it read and navigates to `/papers/digests`. Non-digest notifications retain their existing mark-read behavior. A footer link lets the user open the inbox directly even when no visible digest item is selected.

## Risks / Trade-offs

- [Older notifications contain sparse paper metadata] → Render the available title and arXiv identifier and provide source links; richer cards appear for newly generated digests.
- [Digest items may already exist in the library] → Reuse the idempotent ingestion endpoint and update the card state after a successful request.
- [Unread badge can drift after navigating to the inbox] → Refresh the global unread counter after digest read operations.

