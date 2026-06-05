## Context

The chat toolbar offers knowledge-base mode, web search, and a quick/standard/deep selector. The frontend sends `rag_enabled` and `web_search`, but does not send depth. The streaming backend independently builds RAG context and parses Bing HTML inline. This makes the visible controls misleading and leaves users guessing which combination works.

## Goals / Non-Goals

**Goals:**
- Make enabling web enhancement a one-click action.
- Allow knowledge-base and web retrieval to work together.
- Make quick, standard, and deep modes change retrieval breadth.
- Share retrieval-context construction between streaming and non-streaming chat.
- Keep external web requests bounded and failure-tolerant.

**Non-Goals:**
- Add a new search provider.
- Persist web enhancement between browser sessions.
- Add agentic multi-step browsing.
- Change the language-model provider.

## Decisions

### Treat web search as an enhancement, not an exclusive mode
Knowledge-base and web retrieval SHALL be independently usable and SHALL combine when both are enabled. This supports answers grounded in the user's paper library while still incorporating recent web results.

### Automatically select deep retrieval when enabling web enhancement
The frontend SHALL switch the depth selector to `deep` when a user turns web enhancement on. Users can still choose another depth afterward; the backend SHALL support web retrieval at every depth.

### Send an explicit validated depth parameter
Requests SHALL include `search_depth` with one of `quick`, `standard`, or `deep`. Backend configuration maps the value to retrieval breadth.

### Centralize context assembly
Both streaming and non-streaming endpoints SHALL call a shared helper that adds knowledge-base and web context. This removes divergent behavior and avoids duplicate HTML parsing logic.

### Reuse the bounded web-search service
The existing Bing HTML search service SHALL remain failure-tolerant and SHALL use a short timeout so chat degrades gracefully when the external provider is slow.

## Risks / Trade-offs

- [Risk] Mixed retrieval adds latency → Keep web timeout bounded and vary result count by depth.
- [Risk] Web HTML parsing can break when Bing markup changes → Keep failure graceful and isolate provider parsing in one service.
- [Risk] Deep mode can add more prompt context → Bound knowledge-base and web result counts.
