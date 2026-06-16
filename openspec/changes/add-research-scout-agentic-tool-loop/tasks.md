## 1. Agent Core

- [x] 1.1 Add Research Scout agent state models, tool call models, observation models, and trace event models with validation.
- [x] 1.2 Add a backend Research Scout tool registry with allowed tool names, argument schemas, side-effect policies, and execution hooks.
- [x] 1.3 Implement the bounded agent loop with max steps, timeout, provider-call budgets, invalid-action handling, stop reasons, and deterministic fallback.
- [x] 1.4 Add LLM action planning support through native tool/function calling when available or strict JSON action fallback when not available.

## 2. Search Tools

- [x] 2.1 Convert existing Research Scout intent parsing, query expansion, retrieval, ranking, and evaluation helpers into callable tools or shared utilities.
- [x] 2.2 Ensure arXiv, Semantic Scholar, OpenAlex, and optional Google Scholar tools receive structured year filters and return provider/filter diagnostics.
- [x] 2.3 Add hard-constraint filtering for year, venue, institution, author, dataset, task, and method constraints before final card preparation.
- [x] 2.4 Add recovery behavior that broadens or retries searches when observations show too few candidates or too many constraint exclusions.

## 3. CVF Venue Source

- [x] 3.1 Implement a bounded CVF OpenAccess adapter for CVPR, ICCV, and ECCV venue-year proceedings pages.
- [x] 3.2 Normalize CVF results into `PaperResult` objects with official venue/year/source provenance.
- [x] 3.3 Add title/DOI/arXiv enrichment for CVF candidates while preserving CVF venue evidence and truthful PDF status.
- [x] 3.4 Route CVPR/ICCV/ECCV Research Scout requests to CVF-first discovery before broader scholarly fallback.

## 4. Chat Integration

- [x] 4.1 Replace Research Scout chat orchestration in `chat_sessions.py` with the agent service while preserving response metadata shape where practical.
- [x] 4.2 Stream or attach actual agent trace events including tool arguments summary, source/provider, counts, exclusions, retries, failures, and stop reason.
- [x] 4.3 Keep import, folder, and project actions user-confirmed and prevent autonomous side effects in the agent loop.
- [x] 4.4 Ensure Research Scout source strips include only candidate paper sources used by the final cards.

## 5. Frontend

- [x] 5.1 Update Research Scout trace rendering to display agent tool progress and stop reasons without overcrowding the chat message.
- [x] 5.2 Update candidate card rendering only where new provenance, constraint, or CVF metadata needs to be visible.
- [x] 5.3 Preserve manual-scroll behavior, large chat viewport, and existing card actions during Research Scout streaming.

## 6. Verification

- [x] 6.1 Add backend tests for valid/invalid tool calls, bounded loop stop behavior, deterministic fallback, and side-effect blocking.
- [x] 6.2 Add backend tests proving year filters are passed to providers and known out-of-range candidates are excluded.
- [x] 6.3 Add backend tests proving CVPR/ICCV/ECCV venue requests route to CVF and preserve official venue provenance.
- [x] 6.4 Add backend tests for too-few-results recovery and constraint-exclusion diagnostics.
- [x] 6.5 Update frontend contract tests for agent trace metadata, candidate cards, and Research Scout source strip behavior.
- [x] 6.6 Run OpenSpec validation, focused backend tests, frontend contract tests, and frontend build.
