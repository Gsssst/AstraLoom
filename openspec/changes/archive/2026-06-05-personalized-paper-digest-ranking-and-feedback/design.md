## Context

The digest service currently queries arXiv independently for each subscription keyword, filters results at year granularity, concatenates candidates, and truncates the result list. It does not collapse duplicates across keywords, use the existing scholarly provider aggregator, or read user interaction signals. The digest inbox can ingest papers, but it cannot record recommendation feedback.

## Goals / Non-Goals

**Goals:**
- Produce diverse, deduplicated digest candidates from the existing scholarly providers.
- Prefer genuinely recent papers when precise provider dates are available.
- Rank candidates deterministically with transparent signals that can be shown in the UI.
- Learn from research-project keywords, saved or read papers, and explicit digest feedback.
- Keep feedback persistence lightweight and backward compatible.

**Non-Goals:**
- Train a learning-to-rank model or introduce a vector recommendation pipeline.
- Add a schema migration or a new feedback table.
- Guarantee exact publication dates from providers that do not expose them.
- Redesign the subscription settings page.

## Decisions

### Normalize provider timestamps in `PaperResult`

`PaperResult` will gain an optional ISO publication timestamp. arXiv Atom entries and providers with publication dates will populate it. Scheduled digests will use a bounded freshness window for dated papers while retaining undated provider candidates as lower-confidence fallbacks.

Alternative considered: continue filtering by year. This incorrectly treats every paper published in the current year as newly published.

### Reuse the scholarly provider aggregator

Digest candidate retrieval will call `search_scholarly_papers(source="scholarly")`, which already combines arXiv, Semantic Scholar, OpenAlex, and configured Google Scholar results. Canonical deduplication will run across keyword batches before ranking.

Alternative considered: add separate digest-only provider clients. This would duplicate fallback and deduplication behavior.

### Use an explainable heuristic ranker

The score combines keyword overlap, active research-project keyword overlap, saved/read-paper interest overlap, publication freshness, and source diversity. Explicit dismiss feedback suppresses that canonical paper key in subsequent digests. Each ranked paper stores a short list of reasons.

Alternative considered: call an LLM to rank every candidate. That increases cost and latency and makes recommendations harder to debug.

### Persist feedback inside digest notification metadata

Each digest notification stores a `feedback` map keyed by canonical paper identifier. A category-scoped endpoint validates ownership and updates an allowed action: `interested`, `later`, or `dismissed`. Ranking scans the user's recent digest history for the latest signals.

Alternative considered: introduce a dedicated feedback table. A metadata map is sufficient for the first feedback loop and avoids migration overhead. A separate table remains an option once analytics requirements become clearer.

### Preserve trusted ingestion tokens

New digest recommendation metadata includes provider source, provider remote identifier, and the existing signed remote-ingestion token. The inbox can ingest non-arXiv recommendations through the established personal-ingestion endpoint without refetch ambiguity.

## Risks / Trade-offs

- [Provider timestamps are incomplete] → Treat undated papers as eligible but give them a lower freshness score and show available metadata only.
- [Metadata-based feedback is less queryable than a table] → Keep the payload structured and move to a table only when product analytics require cross-user aggregation.
- [Research profile text can become noisy] → Limit profile terms and use it as a bounded boost rather than the primary score.
- [Older digest metadata lacks provider tokens] → Preserve the existing arXiv fallback ingestion path.

