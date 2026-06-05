## Why

The paper search stack exposes BM25, dense, and hybrid modes, but the modes are not executed consistently: BM25 still invokes dense retrieval, dense mode does not use vector search from the paper API, ranked pagination is truncated, keyword filters are skipped, and the BM25 cache can remain stale after ingestion. Search quality also has no repeatable benchmark, making ranking changes difficult to validate.

## What Changes

- Make `bm25`, `dense`, and `hybrid` modes execute their documented retrieval paths.
- Replace score mixing with weighted reciprocal rank fusion and degrade gracefully when dense retrieval is unavailable.
- Improve academic-term tokenization, title weighting, BM25 cache freshness, ranked pagination, and local keyword filtering.
- Preserve public paper discovery while adding an administrator-only retrieval evaluation endpoint.
- Add a small version-controlled retrieval benchmark and calculate `Recall@K`, `MRR`, and `nDCG@K` per retrieval mode.
- Add regression tests for mode dispatch, fusion, cache invalidation, filters, pagination, and metric calculation.

## Capabilities

### New Capabilities
- `reliable-local-retrieval`: Defines correct, filter-aware, refreshable BM25, dense, and hybrid local paper retrieval behavior.
- `retrieval-quality-evaluation`: Defines repeatable offline retrieval benchmark execution and ranking quality metrics.

### Modified Capabilities

## Impact

- Affected backend modules: hybrid search service, RAG service, paper ingestion service, paper API, and new retrieval evaluation service and benchmark data.
- Existing paper search clients keep the same API shape and gain consistent `search_mode` behavior.
- Evaluation remains an opt-in administrator operation and does not add background model downloads to ordinary read-only browsing.
