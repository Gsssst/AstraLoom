## Why

The project now has enough features; the next quality gains should come from stronger algorithms. Local retrieval and paper recommendations are shared foundations for paper Q&A, writing citation support, research evidence collection, and idea generation, so improving them has broad impact without adding UI surface area.

## What Changes

- Improve local retrieval ranking with query expansion, metadata quality signals, and MMR-style diversity.
- Improve paper evidence chunk retrieval with section-aware scoring and redundant chunk suppression.
- Improve paper recommendation ranking with recency, citation, metadata readiness, user interaction, source diversity, and deduplication signals.
- Keep public API contracts stable and avoid adding new product workflows.

## Capabilities

### New Capabilities

### Modified Capabilities
- `reliable-local-retrieval`: Retrieval SHALL use diversified, metadata-aware ranking for paper and evidence results.
- `personalized-paper-digest-ranking-and-feedback`: Paper recommendations SHALL use user/library feedback and diversity-aware scoring.

## Impact

- Backend services: `hybrid_search.py`, `paper_chunk_service.py`, `paper_selection.py`, and RAG call paths.
- Tests: retrieval quality, paper reader grounding, and paper selection algorithm tests.
- No database migrations or new frontend pages.
