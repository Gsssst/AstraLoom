# Proposal: Paper Reading Workflow

## Why

The project can discover, ingest, and chat with papers, but the post-ingestion reading flow is still fragmented. Users can save papers and the backend already stores a `read_status`, yet the UI does not expose a practical queue for `unread`, `reading`, and `completed` papers. This makes the paper library feel like a search result page instead of a research workspace.

## What Changes

- Add a dedicated reading status workflow in the paper library:
  - Show reading status filters for unread, reading, and completed papers.
  - Show status counts so users can understand their queue at a glance.
  - Let users advance a paper from card actions without opening the detail page.
- Add reading status controls in the paper detail page.
- Keep notes, saved state, chat history, and existing collection behavior compatible.
- Reuse existing `UserPaper.read_status` storage; no database migration is required.

## Out of Scope

- Full reading analytics, calendar planning, and spaced-review scheduling.
- PDF annotation storage beyond the current quote-to-chat behavior.
- Changing the core paper retrieval/ranking algorithm.

## Risks

- The paper library already has many search modes, so the new controls must stay visually compact.
- Status updates should not accidentally remove notes or chat history.
- Static collection routes must remain ordered safely before dynamic paper routes where needed.
