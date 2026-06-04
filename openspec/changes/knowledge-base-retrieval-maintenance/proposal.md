## Why

The paper library can now search with BM25, dense vectors, and hybrid retrieval, but users cannot see whether the library is fully searchable. Missing full text, missing embeddings, and stale lexical indexes silently reduce answer quality and make "why did this query not find anything?" hard to diagnose.

As the knowledge base grows, maintenance needs to be visible and actionable from the product instead of hidden behind developer-only commands.

## What Changes

- Add an administrator knowledge-base maintenance console in settings.
- Expose paper-library health: total papers, full-text coverage, embedding coverage, and BM25 index state.
- Add admin maintenance actions for rebuilding BM25, backfilling missing embeddings, and parsing missing full text in bounded batches.
- Add a search diagnostic tool that compares BM25, dense, and hybrid results for a query and shows coverage signals for each hit.
- Add focused regression tests for route ordering, admin protection, health summaries, diagnostics formatting, and BM25 status reporting.

## Capabilities

### New Capabilities
- `knowledge-base-retrieval-maintenance`: Defines observable, actionable maintenance for paper-library retrieval quality.

## Impact

- Affected backend modules: paper API, hybrid search service, RAG service, and full-text extraction service.
- Affected frontend modules: settings page data tab.
- No database migration is required.
- Maintenance endpoints are administrator-only because they can run model calls or PDF parsing.
