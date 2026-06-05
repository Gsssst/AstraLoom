## Why

The header notification popover is useful for noticing a new digest, but its narrow preview cannot support reading a research digest or deciding which recommended papers belong in the user's library. A dedicated paper-library inbox is needed so digest delivery becomes an actionable discovery workflow instead of a transient alert.

## What Changes

- Add a dedicated paper digest inbox under the paper library for browsing historical daily and test digests.
- Store richer structured paper metadata in new digest notifications so the inbox can render readable recommendation cards.
- Let users open an arXiv abstract page, open the PDF, and add each recommended paper to their personal paper library independently.
- Keep older digest notifications readable even when they only contain the previously stored title and arXiv identifier.
- Turn header digest notifications into a compact entry point that navigates to the digest inbox while preserving unread-state behavior.
- Add a paper-library entry button for the digest inbox with an unread digest badge.

## Capabilities

### New Capabilities
- `paper-digest-inbox`: Dedicated paper-library digest reading, unread handling, and per-paper ingestion workflow.

### Modified Capabilities

## Impact

- Backend API: `app/api/notifications.py`
- Backend digest metadata: `app/services/digest_service.py`
- Frontend routes and layout: `src/App.tsx`, `src/components/AppLayout.tsx`
- Frontend paper library: `src/pages/PapersPage.tsx`, new digest inbox page
- Tests: notification digest regression coverage and frontend build/layout verification
