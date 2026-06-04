## Why

The current chat and paper Q&A web mode performs a single search request and injects an opaque text block. This misses relevant sources for many questions, exposes no web citations to users, and makes the "deep" mode only increase result count rather than search breadth. The frontend also carries TypeScript errors that weaken the project's verification baseline.

## What Changes

- Upgrade the shared web retrieval path used by chat and paper Q&A from one-shot fallback search to bounded multi-query, multi-provider aggregation.
- Preserve structured web search metadata, normalize and deduplicate sources, rank the merged results, and render a concise grounded context for the LLM.
- Return web citations alongside local paper citations so both chat surfaces can display clickable sources.
- Keep quick, standard, and deep modes bounded while making deeper modes increase query breadth.
- Preserve graceful degradation when one search provider or one query fails.
- Remove existing frontend TypeScript errors and require the complete TypeScript build to pass.

## Capabilities

### New Capabilities
- `chat-web-research`: Shared bounded web research retrieval for chat and paper Q&A, including query planning, concurrent provider search, deduplication, grounded context, citations, and degraded operation.
- `frontend-typescript-quality-gate`: A clean full TypeScript build for the frontend application.

### Modified Capabilities

## Impact

- Backend services: `backend/app/services/web_search.py`
- Shared chat retrieval: `backend/app/api/chat_sessions.py`
- Chat and paper Q&A citation rendering in the frontend
- Existing frontend pages and writing components with TypeScript diagnostics
- Backend regression tests for web search and coordinated retrieval
