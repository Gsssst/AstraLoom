## Context

The reported prompt is "请帮我找10篇关于多模态大模型memory的论文". The current Research Scout path detects it as paper discovery, but `_build_research_scout_context` passes the full raw prompt as the only scholarly query. That produces poor results because provider search APIs expect concise English academic terms and do not understand Chinese request scaffolding well. The right search terms depend on the research domain, synonyms, abbreviations, and task names, so the first planning step should be AI-driven.

## Goals / Non-Goals

**Goals:**
- Ask the LLM to convert Chinese/mixed-language paper-finding prompts into a small set of English scholarly query variants.
- Cover common project topics such as 多模态大模型, 视觉语言模型, 大语言模型, 记忆/memory, video grounding.
- Merge results across variants and keep arXiv-enriched candidates preferred.
- Keep latency bounded by limiting planned query count.

**Non-Goals:**
- Full machine translation.
- Full arbitrary translation outside paper discovery.
- Guaranteeing 10 candidates for every niche topic.
- Changing the visible card schema.

## Decisions

1. **LLM query planner first.**
   - The planner receives the original user prompt and parsed intent.
   - It returns strict JSON with concise English scholarly queries, aliases, and optional noisy terms to avoid.
   - This is the right layer for domain synonyms such as `多模态大模型 -> multimodal large language model / MLLM / vision-language model`.

2. **Deterministic fallback remains mandatory.**
   - If the LLM call fails or returns invalid JSON, use conservative local expansions.
   - The fallback keeps Research Scout available under model outages.

3. **Use original query for intent/evaluation.**
   - Candidate relevance and user-visible intent should still reflect what the user asked.
   - Planned queries are retrieval implementation details but can be logged/tool-traced later.

4. **Bounded multi-query search.**
   - Deep scout searches use up to 4 query variants.
   - Each variant fetches enough candidates to fill the final limit after dedupe.

5. **Prefer broad-to-specific variants.**
   - For "多模态大模型 memory", variants include:
     - `multimodal large language model memory`
     - `MLLM memory`
     - `vision language model memory`
     - `memory augmented multimodal large language model`

## Risks / Trade-offs

- **False expansion**: LLM query expansion can drift. Limit the output schema, cap query count, and require concise scholarly terms.
- **More provider calls**: Limit query count and per-query candidate count.
- **Still sparse results**: Some topics remain niche; the system should still show the best available related papers rather than fabricate.
