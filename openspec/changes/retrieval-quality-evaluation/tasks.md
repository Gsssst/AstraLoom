## 1. Local Retrieval Reliability

- [x] 1.1 Add normalized academic tokenization, title weighting, BM25 cache fingerprinting, and explicit invalidation.
- [x] 1.2 Add a unified retrieval mode dispatcher and weighted reciprocal rank fusion with dense-search fallback.
- [x] 1.3 Preserve hybrid ranking scores when reranking is unnecessary and normalize reranker confidence.

## 2. Paper Search API Correctness

- [x] 2.1 Route `bm25`, `dense`, and `hybrid` API modes through the unified dispatcher.
- [x] 2.2 Apply ranked pagination, category filters, and year filters consistently within a bounded candidate window.
- [x] 2.3 Fix remote preview dispatch for arXiv, Semantic Scholar, and combined source searches.
- [x] 2.4 Invalidate the BM25 cache after ingestion and file imports.

## 3. Retrieval Evaluation

- [x] 3.1 Add a version-controlled local retrieval benchmark with stable paper identifiers.
- [x] 3.2 Add retrieval evaluation metrics and an administrator-only on-demand evaluation endpoint.

## 4. Regression Verification

- [x] 4.1 Add focused backend regression tests for tokenization, cache invalidation, mode dispatch, RRF fallback, ranked API behavior, evaluation metrics, and endpoint authorization.
- [x] 4.2 Run backend tests, compile checks, frontend production build, local search smoke checks, and the BM25 retrieval benchmark.
