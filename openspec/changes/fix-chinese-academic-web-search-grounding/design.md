## Context

Chat web research already aggregates structured providers and fallback search engines, then returns the retained results as clickable references. The current planner uses the raw user sentence plus generic suffixes, so Chinese requests with polite/action words can produce low-signal queries and unrelated fallback results.

GitHub reference check:
- Open WebUI groups displayed citations by final document/source metadata and URL, not by raw search prompt text.
- RAGFlow parses answer citation markers separately from source metadata, keeping citations tied to retriever output.

For AstraLoom, the practical lesson is that source display should remain a projection of final retained evidence, while query planning should produce clean, topic-oriented retrieval queries.

## Goals / Non-Goals

**Goals:**
- Convert Chinese academic paper-finding requests into concise topic queries.
- Remove polite/request/count tokens from relevance terms.
- Preserve high-value Chinese topic terms and deterministic English aliases for common AI research topics.
- Keep final references tied to retained `WebSearchResult` records with title, URL, provider, and retrieval query metadata.

**Non-Goals:**
- Replace the web search provider stack.
- Add LLM-based query planning.
- Change chat API response schemas or frontend rendering contracts.
- Guarantee exact paper discovery quality for every field without configured scholarly APIs.

## Decisions

1. Add deterministic query normalization before planning variants.
   - Rationale: It is fast, testable, and works without extra API calls.
   - Alternative considered: ask the LLM to rewrite search queries. Rejected because this path runs before answer generation and should be bounded and reliable.

2. Use small curated alias mappings for common AI research terms.
   - Rationale: Queries like "多模态大模型" benefit from English aliases such as "multimodal large language model" and "MLLM".
   - Alternative considered: broad machine translation. Rejected because no translation dependency exists and incorrect translations can degrade retrieval.

3. Reuse the same normalized topic terms for relevance filtering.
   - Rationale: Filtering should judge against the actual research topic, not request scaffolding such as "请给我找10篇".
   - Alternative considered: only filter by provider rank. Rejected because fallback results can rank unrelated dictionary pages highly.

## Risks / Trade-offs

- Curated aliases can be incomplete -> keep the mechanism additive and fall back to the cleaned Chinese topic.
- Aggressive Chinese stopword removal could remove useful words -> only strip known request scaffolding and keep multi-character topic phrases.
- Some relevant pages may use only English terminology -> add deterministic aliases for the observed multimodal large model case and leave room for later expansions.
