## Context

The current arXiv adapter declares an async method but iterates the synchronous `arxiv.Client.results()` generator. In a live reproduction, the query `video grounding` returned papers after about 42.9 seconds, which is longer than the normal frontend request budget and blocks the event loop while waiting. Direct arXiv API calls are also occasionally slow or rate-limited, and anonymous Semantic Scholar calls can return HTTP 429.

The local-library search path is already stronger than title matching: it combines a title-weighted BM25 index over title and abstract with dense embeddings and weighted reciprocal-rank fusion, degrading to BM25 when embedding coverage is insufficient. This change focuses on remote discovery reliability and ingestion UX.

## Goals / Non-Goals

**Goals:**

- Bound arXiv discovery latency and avoid blocking async request handlers.
- Return useful scholarly candidates when one upstream provider is unavailable.
- De-duplicate provider results using stable identifiers and normalized titles.
- Let an authenticated user add a single discovered paper to their own library without granting administrator bulk-ingestion permissions.
- Keep the provider used for each preview visible to the user.

**Non-Goals:**

- Replace the existing local hybrid retrieval implementation.
- Build a full agentic literature-review pipeline in this change.
- Allow untrusted clients to submit arbitrary paper metadata for storage.

## Decisions

### Use provider adapters and a resilient discovery orchestrator

The arXiv adapter will issue bounded async Atom API requests. A scholarly-search orchestrator will try arXiv first for arXiv searches, then fall back to Semantic Scholar and OpenAlex when necessary. OpenAlex is included because it responds without a credential and remained available during the reproduced rate-limit incident.

Alternative considered: increase the frontend timeout. Rejected because it would leave the event loop blocked and still produce a poor user experience during upstream outages.

### Resolve remote papers server-side before ingestion

Remote preview results expose `source`, a provider-specific `remote_id`, and a short-lived server-signed preview token. The personal-ingestion endpoint verifies the signed preview token before ingesting or de-duplicating the global paper record and marking the resulting paper as saved for the current user. If a token is unavailable, the server can still resolve the selected provider identifier.

Alternative considered: send the complete preview metadata back from the browser. Rejected because clients must not be trusted as a metadata source.

### Preserve administrator-only bulk ingestion

The existing `/papers/ingest` endpoint remains administrator-only. A separate `/papers/ingest-personal` route handles one remote paper at a time for authenticated users.

### Adopt retrieval ideas incrementally

The multi-provider abstraction and canonical aggregation follow the retrieval layering used in PaperQA2 and AI2 ScholarQA. A future change can add ScholarQA-style LLM query rewriting, snippet retrieval, and passage-level reranking after provider reliability is established.

## Risks / Trade-offs

- [Risk] arXiv, Semantic Scholar, and OpenAlex can all be unavailable. → Return a controlled empty result or explicit API error without blocking the server indefinitely.
- [Risk] Fallback results may not have an arXiv PDF. → Store the provider source URL and allow metadata-only ingestion; PDF processing remains conditional on an arXiv ID.
- [Risk] Provider results can overlap. → De-duplicate by arXiv ID, DOI, provider ID, then normalized title.
- [Risk] Normal users can cause new global paper metadata rows. → Restrict the endpoint to one server-resolved paper and reuse existing duplicate checks.

## Migration Plan

1. Deploy settings and provider adapters.
2. Deploy the personal-ingestion route.
3. Deploy the frontend card action.
4. No database migration is required.
