## Context

The local paper retrieval stack was introduced incrementally. `HybridSearchService` can call BM25 and dense search, but API routing and result handling are inconsistent: BM25 mode still invokes dense search, dense mode falls back to SQL text matching, ranked pagination requests too few candidates for later pages, keyword filters are bypassed, and the global BM25 cache never detects new papers. The current weighted score mixing is also labeled RRF even though it depends directly on incomparable raw score distributions.

The system already stores 384-dimensional embeddings and uses `rank-bm25`, so this change can improve correctness and observability without a database migration or new dependency.

## Goals / Non-Goals

**Goals:**
- Make BM25, dense, and hybrid search modes execute predictably.
- Improve lexical matching for academic terms and prioritize title matches.
- Use weighted reciprocal rank fusion with graceful dense-search fallback.
- Keep BM25 results fresh after paper changes.
- Apply filters and pagination after ranked retrieval.
- Add repeatable benchmark metrics for future tuning.

**Non-Goals:**
- Replacing the embedding model or downloading a new reranker model during ordinary searches.
- Building a large human-labeled benchmark in this change.
- Adding a search analytics dashboard.
- Changing remote arXiv or Semantic Scholar ranking algorithms.

## Decisions

### Add a unified retrieval mode dispatcher

`HybridSearchService.search()` dispatches `bm25`, `dense`, or `hybrid`. BM25 mode never calls the embedding model. Dense mode uses pgvector. Hybrid mode executes both and tolerates failure from one branch.

Alternative considered: keep mode branching in the API. Centralizing dispatch keeps RAG and direct paper search behavior aligned.

### Use coverage-aware weighted reciprocal rank fusion

Hybrid mode combines ranked lists with weighted RRF and normalizes the fused score to `[0, 1]`. Rank-based fusion avoids assuming BM25 and cosine similarity scores have the same scale. When embedding coverage is below 80%, hybrid search temporarily degrades to BM25 because a small semantic subset can distort rankings while excluding relevant unembedded papers. Above that threshold, dense weight is conservatively scaled by squared embedding coverage until the library is fully embedded.

Alternative considered: min-max normalization followed by a weighted sum. That approach remains sensitive to outliers and small candidate sets.

### Improve lexical indexing without a new search server

Tokenization uses normalized academic-term tokens instead of whitespace splitting. Title tokens receive additional weight by repetition in the BM25 document representation. The existing in-process index remains appropriate for the current library size.

Alternative considered: introduce PostgreSQL full-text search or an external search service. Those are reasonable later if corpus size warrants operational complexity.

### Refresh BM25 using a cache fingerprint and explicit invalidation

The cache stores a fingerprint derived from paper count and latest update time. Search checks the fingerprint before reuse. Ingestion and import paths explicitly invalidate the cache after successful writes.

### Evaluate stable document identifiers

The benchmark stores arXiv identifiers when available. The evaluation service maps retrieved papers to stable keys, computes `Recall@K`, `MRR`, and `nDCG@K`, and reports per-query rankings. An administrator-only endpoint runs the benchmark on demand.

## Risks / Trade-offs

- [Fingerprint checks add a small database query] -> Accept the cost for correctness while the index remains process-local.
- [Dense mode may need a local embedding model download on first explicit use] -> BM25 remains independent and hybrid mode falls back to lexical retrieval if dense generation fails.
- [A small benchmark can overfit ranking choices] -> Treat the initial cases as a regression floor and expand them as real search failures are observed.
- [Ranked retrieval is capped to a bounded candidate window] -> Use a generous local candidate window and report totals within that ranked window to keep request costs bounded.

## Migration Plan

1. Add the search dispatcher, tokenizer, RRF fusion, fingerprinting, and invalidation hook.
2. Update paper search API dispatch, filtering, pagination, and remote-source handling.
3. Add benchmark data, metrics, and administrator endpoint.
4. Add regression tests and run local BM25 evaluation.

Rollback requires reverting code only; no schema migration is involved.

## Open Questions

- The initial benchmark should grow from observed user queries after the UX workbench refresh.
- Corpus growth may justify PostgreSQL full-text search or a dedicated retrieval service later.
