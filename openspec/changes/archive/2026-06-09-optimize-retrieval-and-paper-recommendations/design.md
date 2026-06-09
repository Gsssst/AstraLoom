## Context

Current retrieval uses process-local BM25 plus dense vector search with RRF fusion. It already degrades when embedding coverage is low, but ranking mostly depends on lexical/vector position. Evidence chunk retrieval is BM25-only and can return adjacent redundant chunks. Paper recommendation uses multi-source recall plus LLM rerank and a simple tag diversity pass.

The user wants algorithm quality improvements, not new features. Open-source systems such as STORM/OpenScholar/PaperQA/SciPIP point to the same useful patterns: expand the query, ground answers in evidence, diversify selected sources, and use user/library signals when ranking papers.

## Goals / Non-Goals

**Goals:**
- Improve retrieval precision and diversity without requiring new infrastructure.
- Keep retrieval deterministic enough to test and reliable when LLM/network calls fail.
- Use existing paper metadata and user interaction rows as recommendation signals.
- Make recommendation scores more interpretable through source labels and balanced selection.

**Non-Goals:**
- No new embedding model, vector index, or cross-encoder dependency.
- No database schema change.
- No new recommendation UI.
- No mandatory network calls for algorithm tests.

## Decisions

1. Add deterministic query expansion before retrieval.
   - Generate lexical variants from the query: original phrase, normalized acronyms/terms, and key academic terms.
   - Avoid LLM-based expansion in the retrieval hot path to keep latency predictable.

2. Add post-fusion quality adjustment.
   - Boost papers with complete metadata, full text, embeddings, citations, and recent years.
   - Cap the boost so relevance still dominates.

3. Add MMR-style diversity after fusion.
   - Select high-scoring papers while penalizing near-duplicate titles/tags/arXiv ids.
   - This improves result breadth for downstream evidence and recommendations.

4. Improve chunk retrieval with section-aware and redundancy-aware scoring.
   - Apply small boosts when detected sections match query intent.
   - Suppress highly overlapping chunks so returned evidence covers more of the paper.

5. Improve recommendation selection with behavioral and library signals.
   - Manual papers remain highest priority.
   - Saved/read/liked local papers, citation count, recency, metadata readiness, and source diversity adjust final selection.
   - External sources remain useful but should not crowd out high-quality local evidence.

## Risks / Trade-offs

- Quality boosts can bury relevant but incomplete papers -> Keep boost weights bounded and apply after core relevance.
- Diversity can skip genuinely similar foundational papers -> Only penalize strong similarity and preserve manual selections.
- User signal availability varies -> Treat missing signals as neutral and keep deterministic fallbacks.
