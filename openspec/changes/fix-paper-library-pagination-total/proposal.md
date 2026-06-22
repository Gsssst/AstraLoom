## Why

The paper library backend returns the full matching count, but the frontend only shows the first 30 loaded records and labels that page count as the library total. Users can verify the database and API contain more papers, but the interface provides no way to move to the remaining pages.

## What Changes

- Display the API-provided total count for paginated paper-library searches instead of the current loaded item count.
- Add pagination controls for local, owned, and remote paper search results.
- Keep collection, saved, reading-list, and maintenance views on their existing list endpoints.
- Reset pagination when the source, filters, sort, or URL-driven search context changes.

## Capabilities

### New Capabilities

### Modified Capabilities
- `paper-discovery-search-and-ingest`: The paper library should expose paginated search totals and navigation accurately for users browsing local and remote results.

## Impact

- Frontend paper-library UI in `frontend/src/pages/PapersPage.tsx`.
- Frontend contract tests for paper-library pagination behavior.
- No backend API or database schema changes.
