## Context

Research Scout now separates requested final count, retrieval pool size, candidate ranking, and frontend card display. However, `_format_research_scout_context` still loops over `candidates[:8]`, so the final LLM can only cite eight candidate blocks even if the retrieval pipeline returned ten or more candidates.

This is a context-formatting bug rather than a provider recall bug. The fix should preserve bounded prompt size while aligning the final context with the user's requested paper count.

## Decisions

1. **Make the context limit explicit.**

   Change `_format_research_scout_context` to accept a `context_limit` argument. The caller computes that limit from Research Scout retrieval metadata instead of allowing the formatter to silently enforce a fixed default.

2. **Use requested final count as the minimum target, with a safety cap.**

   The `prepare_candidate_cards` system context should include:
   - up to the actual candidate count,
   - at least the requested `final_limit` when that many candidates exist,
   - no more than a bounded context cap to avoid oversized prompts.

   The current product cap for final results is already bounded by `RESEARCH_SCOUT_MAX_FINAL_RESULTS`. Use that as the upper context cap so a request capped at fifty can still produce enough candidate evidence for the final answer while staying within product limits.

3. **Tell the model what it is seeing.**

   Add a short context diagnostics line before the candidate blocks, including total ranked candidates and included context candidates. This prevents the final model from mistaking a prompt-window cap for an actual retrieval shortage.

## Risks / Trade-offs

- Larger requested counts increase prompt size. The existing max final-result cap bounds the worst case.
- Some candidates may have long abstracts. The existing per-abstract truncation remains in place to keep the context manageable.

## Verification

- Add a focused backend test that builds ten candidate dictionaries and verifies all ten `[PAPER-N]` blocks are included when the context limit is ten.
- Run OpenSpec validation and the existing Research Scout coordination test file.
