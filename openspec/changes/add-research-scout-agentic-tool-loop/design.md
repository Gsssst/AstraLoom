## Context

Research Scout currently has a mostly deterministic backend pipeline:

```
user query
  -> regex/heuristic intent extraction
  -> LLM planned query strings
  -> arXiv-first search
  -> broad scholarly fallback when sparse
  -> heuristic rank/evaluation
  -> LLM final answer
```

This pipeline is understandable, but it has the same failure mode every time a new constraint appears: the constraint must be threaded manually through each planning, retrieval, fallback, ranking, and display function. Recent failures show `years` and `venues` can be detected in intent yet not enforced by provider calls. For CVPR/ICCV/ECCV queries, arXiv is also the wrong primary source for official venue membership because many arXiv entries do not encode the final conference venue.

The mature pattern used by Claude Code-style coding agents, OpenAI function-calling applications, OpenHands, and PaperQA2 is a bounded observe-plan-act loop:

```
              ┌──────────────────────┐
              │ model chooses action  │
              │ from declared tools   │
              └──────────┬───────────┘
                         │ JSON args
                         ▼
┌──────────────┐   ┌──────────────────────┐   ┌────────────────────┐
│ tool schema  │--▶│ backend validates +   │--▶│ provider/local tool │
│ + policies   │   │ executes call         │   │ observation         │
└──────────────┘   └──────────┬───────────┘   └─────────┬──────────┘
                              │ observation             │
                              └──────────────┬──────────┘
                                             ▼
                                  model decides next step
```

Research Scout should adopt this pattern, but in a constrained way: tools are declared by the backend, arguments are Pydantic-validated, side effects require user confirmation, and the loop has hard limits on steps, provider calls, and latency.

## Goals / Non-Goals

**Goals:**
- Make Research Scout an agentic paper-discovery workflow that can analyze a query, call tools, inspect observations, retry with better queries, and stop with a clear reason.
- Ensure hard constraints such as year, venue, institution, author, dataset, and requested count are represented as structured tool arguments and enforced before final candidate cards.
- Route CVPR/ICCV/ECCV requests to CVF/OpenAccess first, then enrich or fill gaps with arXiv, Semantic Scholar, and OpenAlex.
- Preserve arXiv/PDF preference for importability and reading, without treating arXiv as proof of venue membership.
- Reuse current candidate card, evaluation, source reference, and import-token machinery where practical.
- Expose the actual tool execution trace to the frontend so users can see what the agent did and why.

**Non-Goals:**
- Building a fully general autonomous web-browsing agent.
- Letting the model execute arbitrary URLs, shell commands, or unvalidated provider calls.
- Automatically importing papers, creating folders, or mutating projects without explicit user action.
- Guaranteeing exact recall for every conference/year combination when upstream metadata is unavailable.
- Replacing the paper library search UI.

## Decisions

1. **Introduce a backend Research Scout agent service.**

   Add a service such as `research_scout_agent.py` that owns the loop, state, limits, and trace. `chat_sessions.py` should call this service instead of directly running `_research_scout_intent`, `_plan_research_scout_queries`, and `_retrieve_research_scout_papers`.

   Alternative considered: keep patching the current functions. Rejected because every new constraint requires manual threading and is likely to regress again.

2. **Use a typed tool registry even if the active LLM provider lacks native tool calling.**

   Preferred path: add reusable LLM support for native tool/function calling where the provider supports it. Compatibility path: ask the model to output strict JSON actions matching the same tool schemas, then parse and validate those actions. Both paths feed observations back into the same loop state.

   Tool action shape:

   ```json
   {
     "thought_summary": "Need venue-specific source first.",
     "tool": "search_cvf_openaccess",
     "arguments": {
       "venue": "CVPR",
       "year": 2026,
       "query": "multimodal large language model video understanding",
       "limit": 30
     }
   }
   ```

   The backend must not trust the model's arguments blindly. It validates, clamps limits, normalizes venues, and rejects unknown tools.

3. **Make constraints a first-class state object.**

   The agent maintains a `ResearchScoutState` with:
   - original query
   - requested count
   - normalized topic and expanded aliases
   - year range
   - venues and venue aliases
   - institutions, authors, datasets, tasks, methods
   - hard/soft constraint mode
   - candidates and observations
   - provider call budget

   Tools read and update this state. Final card preparation must enforce hard constraints over this state, not just use them as ranking boosts.

4. **Add a small, explicit tool set.**

   Initial tools:
   - `analyze_research_query`: extract and normalize constraints from the user query.
   - `expand_paper_queries`: produce English scholarly search aliases and task synonyms.
   - `search_arxiv`: call arXiv/arXiv-enriched search with year filters.
   - `search_scholarly`: call Semantic Scholar/OpenAlex/optional Google Scholar with year filters.
   - `search_cvf_openaccess`: search CVF pages for CVPR/ICCV/ECCV venue-year requests and preserve official venue evidence.
   - `search_library`: find existing local papers related to candidates or topic.
   - `filter_candidates`: enforce constraints and explain exclusions.
   - `rank_candidates`: rank deduplicated candidates using query match, venue/year fit, PDF availability, citation, and recency.
   - `evaluate_candidates`: apply existing heuristic and LLM evaluation rubric to the final candidate set.
   - `prepare_candidate_cards`: create frontend-safe cards and import tokens.

   Side-effect tools (`import_paper`, `add_to_folder`, `add_to_project`) remain displayed as available actions but are not callable by the autonomous loop.

5. **CVF/OpenAccess is the official venue adapter for CVPR/ICCV/ECCV.**

   Implement a bounded HTML adapter for `openaccess.thecvf.com` proceedings pages. It should normalize venue/year, parse paper titles/authors/links from official pages, and emit `PaperResult` objects with metadata provenance such as:

   ```json
   {
     "venue": "CVPR",
     "venue_year": 2026,
     "metadata_provenance": {
       "venue": "cvf_openaccess",
       "source_url": "cvf_openaccess"
     }
   }
   ```

   Then use title/DOI/arXiv matching through existing scholarly providers to enrich PDF and citation metadata. If no arXiv PDF is found, the card must show the actual PDF status instead of implying arXiv availability.

6. **Bounded loop and deterministic fallback.**

   The agent loop should use hard safety limits:
   - max 6-8 model/tool turns
   - max provider calls by source
   - max candidates retained in memory
   - timeout per provider and total workflow timeout
   - max final cards clamped by current product limits unless later changed

   If the model emits invalid JSON or repeatedly chooses ineffective tools, the service falls back to deterministic tools: analyze query, route venue source if present, run arXiv + scholarly, filter/rank/evaluate, and explain any shortage.

7. **Trace actual observations, not imagined sources.**

   The frontend should receive trace events corresponding to backend tool executions:
   - `planned`
   - `running`
   - `completed`
   - `failed`
   - `skipped`
   - `needs_confirmation`

   Each event includes tool name, validated arguments summary, provider, result count, excluded count, constraint warnings, retry reason, and stop reason. Source strips in Research Scout messages continue to show only candidate paper sources actually used in cards.

## Risks / Trade-offs

- **More provider calls and latency** -> Use strict budgets, cache repeated provider results, and stop early when validated candidates satisfy the request.
- **LLM chooses poor tools or invalid JSON** -> Validate every action, retry once with error feedback, then use deterministic fallback.
- **CVF HTML changes** -> Keep parser narrow, add tests with fixture HTML, and degrade to scholarly search with explicit "venue unconfirmed" messaging.
- **Venue/year requests may be future or not published** -> Return an evidence-grounded shortage explanation and suggested follow-up queries instead of fabricating papers.
- **Agent trace could become noisy** -> Summarize arguments and counts in the UI while preserving full details in metadata for debugging.
- **Provider metadata conflicts** -> Prefer official venue evidence from CVF for CVPR/ICCV/ECCV, arXiv for arXiv ID/PDF, OpenAlex/Semantic Scholar for citations/institutions, and record provenance.

## Migration Plan

1. Create the agent service and tool registry behind Research Scout mode.
2. Keep existing Research Scout candidate card schema stable where possible.
3. Add CVF adapter and enrich/merge logic.
4. Switch `chat_sessions.py` Research Scout orchestration to the agent service.
5. Update the frontend trace renderer only where the trace schema expands.
6. Keep current deterministic helper functions temporarily as fallback, then remove or fold them into tools after tests pass.

Rollback is straightforward: route Research Scout back to the existing `_build_research_scout_context` pipeline if agent failures exceed tolerance.

## Open Questions

- Should the product limit for requested paper count stay at the current cap, or should Research Scout support larger survey requests such as 50 papers as a paginated/background job?
- Should CVF support start with CVPR/ICCV/ECCV only, or include WACV/ACCV workshops in the same adapter?
- Should agent traces be persisted in chat session history exactly as streamed, or regenerated from message metadata on load?
