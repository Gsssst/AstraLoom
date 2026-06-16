## Context

Research Scout currently uses `RESEARCH_SCOUT_LIMITS` from search depth as the final result count. This hides the user's explicit request: a prompt like "找 10 篇" can still return the standard-depth default of 8. The retrieval stage also uses `per_query_limit = max(limit, 8)`, which makes internal candidate collection too close to the final answer size.

Open-source systems point to a better split:
- PaperQA2 describes paper search as LLM-generated keyword queries followed by evidence gathering and ranking, and notes that an agent may use narrow and broad searches with different phrasing.
- AutoSurvey separates `rag_num` from a much larger `outline_reference_num`, showing that internal literature pools should be larger than the final evidence set.
- AI-Scientist treats Semantic Scholar and OpenAlex as interchangeable literature-search providers, using OpenAlex as a keyless fallback when Semantic Scholar throughput is constrained.

## Goals / Non-Goals

**Goals:**
- Honor explicit requested paper counts up to a bounded cap.
- Keep Research Scout fast for ordinary 5-12 paper searches while supporting larger "调研 50 篇" requests.
- Increase recall for video grounding by adding common task aliases.
- Expose retrieval diagnostics so the UI and generated answer can explain whether a request was capped or under-filled.
- Fix candidate card overflow and remove the six-card display cap without flooding the initial viewport.

**Non-Goals:**
- Add new scholarly providers.
- Change database schema or ingestion tokens.
- Ask the LLM to deeply evaluate all 50 candidates; detailed LLM calibration remains bounded to top candidates.
- Build a dedicated literature-review workspace. This change only improves chat Research Scout behavior.

## Decisions

1. **Parse requested count from the prompt.**
   - Add a helper that recognizes Chinese and English count forms such as `10 篇`, `50 papers`, `十篇`, `几十篇`.
   - Use depth defaults only when no explicit count is present.
   - Cap final results at 50 for now. This covers practical "调研一批论文" use without making one chat turn too slow or expensive.

2. **Separate final count from candidate-pool size.**
   - Compute `final_limit` from requested count or depth defaults.
   - Compute `pool_target` and `per_query_limit` from `final_limit`, with oversampling for ranking and deduplication.
   - Keep provider calls bounded: multiple query strings times multiple providers can grow quickly.

3. **Broaden topic aliases before searching.**
   - Add a topic alias map for video grounding: `natural language video localization`, `temporal sentence grounding`, `moment localization`, `video moment retrieval`, `text-to-video moment retrieval`, and related terms.
   - Merge LLM-planned queries with deterministic aliases so the system still behaves well when the LLM planner fails.

4. **Escalate fallback when the ranked set is under-filled.**
   - First run arXiv-enriched search.
   - If under-filled, run broad scholarly fallback.
   - If still under-filled and the requested count is larger than the ranked set, retry with broader aliases and a larger per-query limit within bounds.

5. **Keep LLM evaluation bounded.**
   - Continue LLM-calibrating only the top six candidates for detailed card scores.
   - Use heuristic evaluations for the rest. This avoids sending 50 abstracts to the model in one turn.

6. **Improve card display progressively.**
   - Show up to 10 candidate cards initially.
   - If more exist, provide a compact "展开全部 / 收起" control.
   - Style long tags inside metadata/provenance/constraint rows with max-width and ellipsis.

## Risks / Trade-offs

- Larger requested counts may increase latency and provider usage. Mitigation: cap final count, cap per-query result size, and expose retrieval diagnostics.
- Broad aliases can introduce less-related papers. Mitigation: rank by query-match, arXiv/PDF availability, citations, recency, and constraints.
- Returning 50 cards can overwhelm the chat. Mitigation: progressive display and bounded initial cards.
- LLM evaluation only covers top candidates. Mitigation: mark the evaluation source and keep heuristic scores for lower-ranked cards.
