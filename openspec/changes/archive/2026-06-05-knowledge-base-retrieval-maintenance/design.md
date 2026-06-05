## Context

The current retrieval stack has correctness improvements and an admin benchmark endpoint, but operational state is still opaque. A paper can be present in the library while missing parsed full text or vector embeddings. Hybrid search also intentionally degrades to BM25 when embedding coverage is low. These are sensible safeguards, but users need to see and repair the underlying state.

The settings data tab already contains data-management affordances, so it is the lowest-friction home for a first maintenance console.

## Goals / Non-Goals

**Goals:**
- Show retrieval health in one place.
- Make common repair operations available without a terminal.
- Keep repair operations bounded so a click does not start an unbounded expensive job.
- Explain search results by retrieval branch and per-paper coverage signals.
- Keep all mutating or potentially expensive operations admin-only.

**Non-Goals:**
- Building a background job queue in this change.
- Replacing BM25/Dense/Hybrid algorithms.
- Adding a dedicated search server.
- Automatically downloading every missing PDF in the library.

## Decisions

### Add explicit maintenance endpoints

Use `/api/papers/maintenance/*` fixed routes before `/{paper_id}`. This prevents dynamic paper-id routing from accidentally catching maintenance paths and matches the existing route-ordering convention.

### Health summary remains cheap

The health endpoint uses aggregate SQL counts and the process-local BM25 status helper. It does not parse PDFs or call the embedding model. It returns small samples of missing full text and embeddings to guide manual repair.

### Bounded repair batches

Embedding and full-text backfills accept small limits. The frontend defaults to conservative values. This keeps API calls observable and avoids surprise long-running work.

### Diagnostics compare retrieval branches

Diagnostics run BM25, dense, and hybrid for the same query and format each result with score, title, year, source, and coverage flags. The output is not a benchmark; it is a quick explanation tool for observed bad queries.

## Risks / Trade-offs

- [Backfilling embeddings can be slow or fail if the embedding model is unavailable] -> Return success/failure counts and keep batch limits small.
- [Full-text parsing may fail for papers without a reachable PDF] -> Report skipped/errors instead of blocking other papers.
- [BM25 status is process-local] -> Present it as current-server state, not a durable database index.

## Migration Plan

1. Add BM25 status helper and maintenance response formatting helpers.
2. Add fixed admin endpoints for health, rebuild, backfill, and diagnostics.
3. Add the settings data-tab maintenance console.
4. Add focused backend tests and run frontend/backend verification.
