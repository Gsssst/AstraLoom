## Context

The prompt "请帮我找10篇关于多模态大模型memory的论文" now routes into Research Scout and gets LLM-planned English queries. The remaining failure is retrieval strategy: the current path calls only `arxiv_enriched`. That source starts from strict arXiv matches and enriches those matches, so when arXiv returns zero or too few papers, Semantic Scholar/OpenAlex cannot contribute candidates even if they know relevant work.

Open-source research assistants use a broader pattern:

- PaperQA2 exposes paper search as a repeatable tool with query offsets and keeps adding papers when evidence is insufficient.
- GPT Researcher first plans sub-queries, then runs each query across configured retrievers and continues when one source has no result.
- STORM generates search queries from the question, retrieves across sources, and refuses to fabricate when retrieval is empty.
- AI-Scientist v2 uses Semantic Scholar tooling for paper context instead of relying on a single arXiv-only path.

The product constraint remains arXiv/PDF preference: arXiv papers are usually easiest to import and read, but non-arXiv scholarly candidates are still better than returning no cards for a valid request.

## Goals / Non-Goals

**Goals:**
- Keep arXiv-enriched retrieval as the first pass.
- Add broad scholarly fallback when arXiv-enriched results are below the requested candidate target.
- Merge and rank arXiv, Semantic Scholar, OpenAlex, and Google Scholar candidates without duplicate cards.
- Prefer PDF/arXiv candidates while allowing non-arXiv scholarly candidates with clear source/PDF status.
- Expose retrieval strategy in the existing tool trace.

**Non-Goals:**
- New provider integrations.
- Full reranker service or embedding-based reranking.
- Guaranteeing exactly 10 results for every topic.
- Changing the candidate card action model.

## Decisions

1. **Two-stage retrieval inside Research Scout.**
   - Stage 1 uses `source="arxiv_enriched"` for each planned query.
   - If deduplicated results are fewer than the final limit, Stage 2 uses `source="scholarly"` for the same planned queries.
   - This mirrors GPT Researcher/PaperQA2 style recovery: when current evidence is insufficient, continue retrieval with broader sources.

2. **Rank after merge, not per provider.**
   - After both stages, merge with existing `deduplicate_papers`.
   - Apply lightweight Research Scout ranking before truncating: query matches, arXiv/PDF availability, citation count, and recency.
   - This preserves arXiv preference without hiding all non-arXiv candidates.

3. **Trace the actual strategy.**
   - Tool trace should say whether broad fallback ran, which providers were involved, and how many candidates were produced.
   - This gives the user an explanation when results include non-arXiv papers.

4. **No generic web fallback in Research Scout.**
   - Fallback remains scholarly-provider fallback only.
   - Generic web references must not reappear in the source strip for Research Scout answers.

## Risks / Trade-offs

- **More API calls** -> Cap planned queries and per-query result count using the existing Research Scout limits.
- **Lower precision from broad providers** -> Rank by query match and source/PDF signals before cards are generated.
- **Non-arXiv papers may lack PDFs** -> Card metadata must keep PDF status visible and avoid claiming import/readiness beyond available data.
- **Provider outage** -> Continue with other planned queries and sources, logging failed groups without failing the whole chat turn.
