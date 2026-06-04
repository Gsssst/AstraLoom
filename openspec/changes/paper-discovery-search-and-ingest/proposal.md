## Why

The paper-library arXiv preview currently performs a synchronous upstream request inside an async API handler. Slow or rate-limited arXiv responses can block the backend long enough for the frontend request to fail, and discovered papers expose an ingest action only to administrators.

## What Changes

- Replace blocking arXiv discovery with bounded asynchronous requests.
- Add resilient scholarly discovery fallback through Semantic Scholar and OpenAlex, with canonical de-duplication across providers.
- Expose the actual discovery provider in preview results so fallback behavior remains understandable.
- Add a narrow authenticated endpoint that resolves one remote paper server-side, stores it if needed, and saves it into the current user's paper library.
- Show a one-click “加入论文库” action on remote preview cards for authenticated users while retaining administrator-only bulk ingestion.
- Improve frontend error messages for upstream discovery failures.

## Capabilities

### New Capabilities

- `paper-discovery-search-and-ingest`: Resilient remote scholarly search and authenticated one-click personal paper ingestion.

### Modified Capabilities

None.

## Impact

- Backend search providers, paper ingestion service, paper API routes, and settings.
- Paper-library frontend remote search cards.
- Optional Semantic Scholar API-key configuration. OpenAlex remains usable without a key.

